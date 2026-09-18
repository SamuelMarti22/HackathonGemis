-- Esquema placeholder para la base de datos de Lexi.
-- Aún no hay lógica de negocio: estas tablas solo dejan mapeado
-- dónde vivirán los casos, documentos y la fuente del RAG normativo.

CREATE TABLE IF NOT EXISTS casos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID,
    relato TEXT,
    creado_en TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS documentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    caso_id UUID REFERENCES casos(id),
    tipo TEXT, -- 'derecho_peticion' | 'tutela'
    estado TEXT, -- 'borrador' | 'listo_para_revisar'
    contenido TEXT,
    creado_en TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS normas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo TEXT,
    referencia TEXT,
    url TEXT
);
