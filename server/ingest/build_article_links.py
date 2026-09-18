"""
Construye un mapeo artículo -> URL oficial, para poder citar cada norma con
un hipervínculo verificable (requisito del README).

Fuente: Secretaría del Senado de Colombia, que publica la Constitución
paginada en HTML con anclas por artículo:
  http://www.secretariasenado.gov.co/senado/basedoc/constitucion_politica_1991_pr0XX.html#<ancla>

Se descargan las páginas UNA VEZ en tiempo de build (no en runtime del
chatbot) y se guarda el resultado en server/data/article_links.json, que se
versiona en el repo. Vuelve a ejecutar este script sólo si la Secretaría del
Senado cambia su paginación.

Uso:
    python -m ingest.build_article_links
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = "http://www.secretariasenado.gov.co/senado/basedoc/constitucion_politica_1991_pr{:03d}.html"
# Los artículos 1 a 32 están únicamente en la página "índice" (no en pr001).
FIRST_PAGE_URL = "http://www.secretariasenado.gov.co/senado/basedoc/constitucion_politica_1991.html"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "article_links.json"
MAX_PAGES = 40  # se detiene al primer 404; 15 páginas conocidas a 2026-09

ANCHOR_RE = re.compile(r'<a class="bookmarkaj" name="([^"]+)"', re.IGNORECASE)
TRANSITORIO_ANCHOR_RE = re.compile(r"^TRANSITORIO\s+(\d+[A-Za-z]?)$", re.IGNORECASE)
NUMERIC_ANCHOR_RE = re.compile(r"^\d+[A-Za-z]?$")


def fetch(url: str) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (RAG ingest script)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    return raw.decode("iso-8859-1")


def build_links() -> dict:
    articulo_links: dict[str, str] = {}
    transitorio_links: dict[str, str] = {}

    def scan(url: str, html: str) -> None:
        for anchor in ANCHOR_RE.findall(html):
            frag = urllib.parse.quote(anchor)
            link = f"{url}#{frag}"
            m_trans = TRANSITORIO_ANCHOR_RE.match(anchor)
            if m_trans:
                transitorio_links.setdefault(m_trans.group(1), link)
            elif NUMERIC_ANCHOR_RE.match(anchor):
                articulo_links.setdefault(anchor, link)

    first_html = fetch(FIRST_PAGE_URL)
    if first_html:
        print(f"  índice (artículos 1-32): {len(first_html)} bytes")
        scan(FIRST_PAGE_URL, first_html)

    for page_num in range(1, MAX_PAGES + 1):
        url = BASE_URL.format(page_num)
        html = fetch(url)
        if html is None:
            break
        print(f"  pr{page_num:03d}: {len(html)} bytes")
        scan(url, html)

    return {
        "source": "Secretaría del Senado de Colombia",
        "base_pattern": BASE_URL,
        "articulo": articulo_links,
        "transitorio": transitorio_links,
        "fallback_url": BASE_URL.format(1),
    }


def main() -> None:
    print("Descargando páginas de la Constitución (Secretaría del Senado) ...")
    data = build_links()
    print(f"  -> {len(data['articulo'])} artículos, {len(data['transitorio'])} transitorios con enlace")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Guardado en {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
