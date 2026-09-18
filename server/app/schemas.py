from pydantic import BaseModel, Field

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


class RespuestaJuridicaLLM(BaseModel):
    hay_normas_aplicables: bool = Field(
        description="False si ninguno de los artículos en CANDIDATOS aplica realmente al caso"
    )
    normas_aplicables: list[NormaAplicadaLLM]
    recomendaciones: list[str] = Field(
        description="Pasos concretos y accionables que la persona puede seguir"
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


class RespuestaJuridica(BaseModel):
    hay_normas_aplicables: bool
    normas_aplicables: list[NormaCitada]
    recomendaciones: list[str]
    disclaimer: str = DISCLAIMER
