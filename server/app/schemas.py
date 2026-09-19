from typing import Literal

from pydantic import BaseModel, Field

# Mecanismos de protección ciudadana que el modelo puede recomendar, y el
# artículo constitucional que los consagra (se resuelve contra la base de
# datos real, nunca se confía en lo que "diga" el modelo sobre el artículo).
MECANISMOS = {
    "tutela": {"nombre": "Acción de tutela", "articulo_base": "86"},
    "derecho_de_peticion": {"nombre": "Derecho de petición", "articulo_base": "23"},
    "accion_de_cumplimiento": {"nombre": "Acción de cumplimiento", "articulo_base": "87"},
    "accion_popular": {"nombre": "Acción popular", "articulo_base": "88"},
    "habeas_corpus": {"nombre": "Habeas corpus", "articulo_base": "30"},
    "habeas_data": {"nombre": "Habeas data", "articulo_base": "15"},
}
MecanismoTipo = Literal[
    "tutela",
    "derecho_de_peticion",
    "accion_de_cumplimiento",
    "accion_popular",
    "habeas_corpus",
    "habeas_data",
]

DISCLAIMER = (
    "Esta herramienta es un apoyo educativo basado en la Constitución Política de "
    "Colombia y no reemplaza a un abogado. Para tu caso concreto, consulta con un "
    "profesional del derecho o con un consultorio jurídico."
)


class ChatRequest(BaseModel):
    mensaje: str = Field(min_length=1, max_length=4000)


# --- Esquema que le pedimos al modelo (salida estructurada) ---
# El modelo NUNCA produce la URL ni el texto completo del artículo: sólo
# elige, de la lista de candidatos que le dimos, cuáles aplican. El backend
# reconstruye la cita y el enlace desde la base de datos, así que el modelo
# no puede "inventarse" un artículo o un link que no exista.


class NormaAplicadaLLM(BaseModel):
    numero_articulo: str = Field(
        description="Número exacto de un artículo tomado de la lista CANDIDATOS. Nunca inventar."
    )
    tipo: str = Field(description='"articulo" o "transitorio", tal como aparece en CANDIDATOS')
    por_que_aplica: str = Field(description="Explicación breve de por qué este artículo aplica al caso")


class MecanismoRecomendadoLLM(BaseModel):
    tipo: MecanismoTipo = Field(
        description="El mecanismo de protección ciudadana más adecuado para este caso concreto"
    )
    justificacion: str = Field(
        description="Por qué este mecanismo (y no otro de la lista) es el más adecuado para el caso"
    )


class RespuestaJuridicaLLM(BaseModel):
    hay_normas_aplicables: bool = Field(
        description="False si ninguno de los artículos en CANDIDATOS aplica realmente al caso"
    )
    normas_aplicables: list[NormaAplicadaLLM]
    recomendaciones: list[str] = Field(
        description="Pasos concretos y accionables que la persona puede seguir"
    )
    mecanismo_recomendado: MecanismoRecomendadoLLM | None = Field(
        default=None,
        description=(
            "Obligatorio (no null) cuando hay_normas_aplicables es true: el mecanismo de "
            "protección ciudadana más adecuado, elegido entre tutela, derecho_de_peticion, "
            "accion_de_cumplimiento, accion_popular, habeas_corpus o habeas_data. "
            "Null sólo si hay_normas_aplicables es false."
        ),
    )


# --- Lo que efectivamente devuelve la API (ya enriquecido y verificado) ---


class NormaCitada(BaseModel):
    citation: str
    tipo: str
    titulo: str | None
    capitulo: str | None
    url: str | None
    por_que_aplica: str
    extracto: str


class MecanismoRecomendado(BaseModel):
    tipo: MecanismoTipo
    nombre: str
    justificacion: str
    articulo_base: str
    articulo_base_url: str | None


class RespuestaJuridica(BaseModel):
    hay_normas_aplicables: bool
    normas_aplicables: list[NormaCitada]
    recomendaciones: list[str]
    mecanismo_recomendado: MecanismoRecomendado | None = None
    disclaimer: str = DISCLAIMER


class DocumentoGenerado(BaseModel):
    tipo: MecanismoTipo
    titulo: str
    explicacion_mecanismo: str
    cuerpo: str
    normas_citadas: list[str] = Field(default_factory=list)


class DocumentoGeneradoLLM(BaseModel):
    titulo: str = Field(description="Título corto del documento, ej. 'Acción de tutela por derecho a la salud'")
    explicacion_mecanismo: str = Field(
        description="2-4 frases dirigidas a la persona explicando qué es este mecanismo y por qué es el adecuado"
    )
    cuerpo: str = Field(
        description=(
            "Texto completo del documento legal, listo para editar. Usa placeholders entre "
            "corchetes para datos que no se conocen: [Nombre completo], [Número de cédula], "
            "[Dirección], [Ciudad], [Fecha]. SOLO cita los artículos de la lista de artículos "
            "verificados que se te dan; nunca otro número de artículo."
        )
    )
