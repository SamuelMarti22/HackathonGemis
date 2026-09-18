"""
Parsea el PDF de la Constitución Política de Colombia en artículos individuales.

Usa `pdftotext -layout` (poppler-utils) para extraer el texto respetando el
orden de lectura, luego:
  1. Filtra encabezados/pies de página repetidos (ruido de paginación).
  2. Detecta encabezados reales de Título/Capítulo para dar contexto a cada
     artículo (a qué título y capítulo pertenece).
  3. Detecta el inicio de cada "Artículo N." (cuerpo principal) y
     "ARTÍCULO TRANSITORIO N." (disposiciones transitorias) por separado,
     ya que ambas series de numeración empiezan en 1 y no deben mezclarse.

Salida: server/data/articles.json — lista de artículos con metadata, lista
para generar embeddings e insertar en la base de datos.

Uso:
    python -m ingest.parse_constitution [ruta_pdf] [ruta_salida_json]
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import os

# En local (fuera de Docker) el PDF vive en <repo>/RAG/; dentro del contenedor
# se monta en /app/RAG (ver docker-compose.yml), así que se puede sobreescribir
# con la variable de entorno PDF_PATH.
DEFAULT_PDF = Path(
    os.environ.get("PDF_PATH")
    or Path(__file__).resolve().parent.parent.parent / "RAG" / "COLOMBIA-Constitucion.pdf"
)
DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "data" / "articles.json"

# Líneas de ruido: separadores, encabezado de página repetido, números de página sueltos.
NOISE_LINE_RE = re.compile(
    r"""^(
        [_\s]{5,}                                  # línea de guiones bajos
        |Constitución\ Pol[ií]tica\ de\ Colombia\s*$
        |\d{1,4}\s*$                                # número de página suelto
    )$""",
    re.VERBOSE,
)

# Pie de página repetido tipo "  De los Derechos ...        Artículos 40 - 42"
# o, en artículos largos que ocupan varias páginas, sólo "... Artículo 361" /
# "... Artículo Transitorio" sin rango. Siempre precedido por un salto de
# columna (>=4 espacios) para no confundirlo con una referencia inline como
# "... creada por el artículo 38" dentro del cuerpo de un artículo.
RUNNING_FOOTER_RE = re.compile(
    r"\s{4,}art[íi]culos?\s+(transitorios?\s*)?(\d+[A-Za-z]?\s*(-\s*\d+[A-Za-z]?)?)?\s*$",
    re.IGNORECASE,
)

TITULO_HEADER_RE = re.compile(r"^\s*T[ÍI]TULO\s+([IVXLCDM]+)\s*$")
CAPITULO_HEADER_RE = re.compile(r"^\s*CAP[ÍI]TULO\s+([0-9IVXLCDM]+)\s*$")
DISPOSICIONES_TRANSITORIAS_RE = re.compile(r"^\s*DISPOSICIONES\s+TRANSITORIAS\s*$")
# Marca el final del articulado: lista de integrantes de la Asamblea
# Nacional Constituyente que cierra la edición del PDF (no es texto normativo).
END_OF_DOCUMENT_RE = re.compile(r"^\s*COMISI[ÓO]N\s+[IVXLCDM]+\s*$")

ARTICULO_START_RE = re.compile(r"^Art[íi]culo\s+(\d+[A-Za-zº°]?)\.\s*(.*)$")
ARTICULO_TRANSITORIO_START_RE = re.compile(
    r"^ART[ÍI]CULO\s+TRANSITORIO\s+(\d+[A-Za-zº°]?)\.\s*(.*)$"
)
# Algunos Actos Legislativos posteriores añaden un "artículo transitorio" sin
# número de secuencia propio (ej. entre el 61 y el 66 de la edición 2016).
ARTICULO_TRANSITORIO_UNNUMBERED_RE = re.compile(r"^ART[ÍI]CULO\s+TRANSITORIO\.\s*(.*)$")
ACTO_LEGISLATIVO_REF_RE = re.compile(r"Acto\s+Legislativo\s+\d+\s+de\s+\d{4}", re.IGNORECASE)

LIST_ITEM_RE = re.compile(r"^(\d+[°º]?[.\)]|[a-z]\)|PAR[ÁA]GRAFO\b|Par[áa]grafo\b)")


@dataclass
class Article:
    kind: str  # "articulo" | "transitorio"
    number: str  # "1", "35", "380"
    citation: str  # "Artículo 100" | "Artículo transitorio 5"
    titulo: str | None
    capitulo: str | None
    text: str


def run_pdftotext(pdf_path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        capture_output=True,
        check=True,
    )
    return result.stdout.decode("utf-8", errors="replace")


def is_all_caps_heading(line: str) -> bool:
    stripped = line.strip()
    if len(stripped) < 3:
        return False
    letters = [c for c in stripped if c.isalpha()]
    if not letters:
        return False
    return all(c.isupper() for c in letters)


def normalize_body(lines: list[str]) -> str:
    paragraphs: list[str] = []
    current: list[str] = []
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if LIST_ITEM_RE.match(stripped) and current:
            paragraphs.append(" ".join(current))
            current = [stripped]
        else:
            current.append(stripped)
    if current:
        paragraphs.append(" ".join(current))
    return "\n".join(p for p in paragraphs if p)


def parse_articles(raw_text: str) -> list[Article]:
    lines = raw_text.split("\n")

    articles: list[Article] = []

    current_titulo: str | None = None
    current_capitulo: str | None = None
    current_kind: str | None = None  # None hasta encontrar "Artículo 1."
    current_number: str | None = None
    current_body_lines: list[str] = []
    current_citation_override: str | None = None
    unnumbered_transitorio_count = 0
    last_articulo_num = 0
    last_transitorio_num = 0

    def leading_int(number: str) -> int:
        m = re.match(r"\d+", number)
        return int(m.group(0)) if m else 0

    # Estado auxiliar para capturar el nombre debajo de "TÍTULO N" / "CAPÍTULO N"
    pending_titulo_num: str | None = None
    pending_capitulo_num: str | None = None

    def flush_article() -> None:
        nonlocal current_number, current_body_lines, current_kind, current_citation_override
        if current_kind is None or current_number is None:
            return
        text = normalize_body(current_body_lines)
        if not text:
            current_body_lines = []
            current_citation_override = None
            return
        citation = current_citation_override or (
            f"Artículo {current_number}"
            if current_kind == "articulo"
            else f"Artículo transitorio {current_number}"
        )
        articles.append(
            Article(
                kind=current_kind,
                number=current_number,
                citation=citation,
                titulo=current_titulo,
                capitulo=current_capitulo,
                text=text,
            )
        )
        current_citation_override = None
        current_body_lines = []

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]

        if END_OF_DOCUMENT_RE.match(line):
            break

        if NOISE_LINE_RE.match(line) or RUNNING_FOOTER_RE.search(line):
            i += 1
            continue

        stripped = line.strip()

        if DISPOSICIONES_TRANSITORIAS_RE.match(line):
            flush_article()
            current_titulo = "Disposiciones transitorias"
            current_capitulo = None
            i += 1
            continue

        m_titulo = TITULO_HEADER_RE.match(line)
        if m_titulo:
            pending_titulo_num = m_titulo.group(1)
            i += 1
            continue

        if pending_titulo_num is not None:
            if stripped == "":
                i += 1
                continue
            if is_all_caps_heading(line):
                flush_article()
                current_kind = None
                current_number = None
                name_parts = [stripped]
                i += 1
                while i < n and is_all_caps_heading(lines[i]):
                    name_parts.append(lines[i].strip())
                    i += 1
                current_titulo = f"Título {pending_titulo_num}: {' '.join(name_parts).title()}"
                current_capitulo = None
                pending_titulo_num = None
                continue
            pending_titulo_num = None  # no era el título esperado, seguir normal

        m_capitulo = CAPITULO_HEADER_RE.match(line)
        if m_capitulo:
            pending_capitulo_num = m_capitulo.group(1)
            i += 1
            continue

        if pending_capitulo_num is not None:
            if stripped == "":
                i += 1
                continue
            if is_all_caps_heading(line):
                flush_article()
                current_kind = None
                current_number = None
                name_parts = [stripped]
                i += 1
                while i < n and is_all_caps_heading(lines[i]):
                    name_parts.append(lines[i].strip())
                    i += 1
                current_capitulo = f"Capítulo {pending_capitulo_num}: {' '.join(name_parts).title()}"
                pending_capitulo_num = None
                continue
            pending_capitulo_num = None

        m_art = ARTICULO_START_RE.match(stripped)
        # Los números de artículo son estrictamente crecientes en el texto real;
        # esto filtra falsos positivos como una referencia "Artículo 1°." citada
        # dentro del cuerpo de un artículo muy posterior (ej. el 250).
        if m_art and leading_int(m_art.group(1)) <= last_articulo_num:
            m_art = None

        m_art_trans = ARTICULO_TRANSITORIO_START_RE.match(stripped)
        if m_art_trans and leading_int(m_art_trans.group(1)) <= last_transitorio_num:
            m_art_trans = None

        m_art_trans_unnum = (
            None if m_art_trans else ARTICULO_TRANSITORIO_UNNUMBERED_RE.match(stripped)
        )

        if m_art_trans:
            flush_article()
            current_kind = "transitorio"
            current_number = m_art_trans.group(1)
            last_transitorio_num = leading_int(current_number)
            current_body_lines = [m_art_trans.group(2)] if m_art_trans.group(2) else []
            i += 1
            continue

        if m_art_trans_unnum:
            flush_article()
            unnumbered_transitorio_count += 1
            current_kind = "transitorio"
            current_number = f"s/n-{unnumbered_transitorio_count}"
            rest = m_art_trans_unnum.group(1)
            ref = ACTO_LEGISLATIVO_REF_RE.search(rest)
            current_citation_override = (
                f"Artículo transitorio ({ref.group(0)})"
                if ref
                else f"Artículo transitorio (sin número {unnumbered_transitorio_count})"
            )
            current_body_lines = [rest] if rest else []
            i += 1
            continue

        if m_art:
            flush_article()
            current_kind = "articulo"
            current_number = m_art.group(1)
            last_articulo_num = leading_int(current_number)
            current_body_lines = [m_art.group(2)] if m_art.group(2) else []
            i += 1
            continue

        if current_kind is not None:
            current_body_lines.append(line)

        i += 1

    flush_article()
    return merge_duplicates(articles)


def merge_duplicates(articles: list[Article]) -> list[Article]:
    """Algunos artículos aparecen dos veces en el PDF: una vez citados dentro
    del texto de un Acto Legislativo que los reforma ("... quedará así:") y
    otra vez como el artículo resultante. Se fusionan en un solo chunk para
    no duplicar la cita en la búsqueda."""
    merged: dict[tuple[str, str], Article] = {}
    order: list[tuple[str, str]] = []
    for a in articles:
        key = (a.kind, a.number)
        if key not in merged:
            merged[key] = a
            order.append(key)
        else:
            existing = merged[key]
            merged[key] = Article(
                kind=existing.kind,
                number=existing.number,
                citation=existing.citation,
                titulo=existing.titulo or a.titulo,
                capitulo=existing.capitulo or a.capitulo,
                text=existing.text + "\n\n" + a.text,
            )
    return [merged[k] for k in order]


def main() -> None:
    pdf_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PDF
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT

    print(f"Leyendo {pdf_path} ...")
    raw_text = run_pdftotext(pdf_path)

    print("Parseando artículos ...")
    articles = parse_articles(raw_text)

    n_articulos = sum(1 for a in articles if a.kind == "articulo")
    n_transitorios = sum(1 for a in articles if a.kind == "transitorio")
    print(f"  -> {n_articulos} artículos + {n_transitorios} artículos transitorios")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump([asdict(a) for a in articles], f, ensure_ascii=False, indent=2)

    print(f"Guardado en {output_path}")


if __name__ == "__main__":
    main()
