# HackathonGemis — Lexi

Tutor jurídico: el usuario describe su caso en lenguaje natural y recibe
orientación basada en un RAG propio sobre la Constitución Política de
Colombia.

## Funcionalidades

- El usuario ingresa su caso en lenguaje natural y recibe:
  - Resumen de la situación en términos legales, mostrado en streaming.
  - Norma o normativas aplicables, citadas de forma identificable, con un
    hipervínculo para ir a leer la norma en cuestión.
  - Recomendaciones o pasos a seguir.
  - Un aviso visible de que la herramienta no es un abogado como tal.
- El usuario puede pedir generar un derecho de petición o tutela:
  - Puede editarlo antes de descargarlo.
  - Puede descargarlo después de aceptarlo.
- Se alimenta de un RAG propio (Postgres/pgvector sobre la Constitución).
- Arranque con Docker: client, server, BD.

## Arquitectura

```
client/  React + Vite + Tailwind — chat, normativa, recomendaciones, documentos.
server/  FastAPI — RAG (Postgres/pgvector) + memoria de conversación (MongoDB) + Gemini.
RAG/     Fuente (PDF de la Constitución) que alimenta el índice del RAG.
```

Detalle del backend (diseño anti-alucinación, pipeline de ingesta, etc.) en
[`server/README.md`](server/README.md).

## Estado de la integración frontend ↔ backend

| Funcionalidad | Endpoint | Estado |
| --- | --- | --- |
| Resumen del caso (streaming) | `POST /cases/{id}/chat` (SSE `event: resumen`) | Conectado |
| Normativa aplicable + enlaces | `POST /cases/{id}/chat` (SSE `event: normas`) | Conectado |
| Recomendaciones | `POST /cases/{id}/chat` (SSE `event: normas`) | Conectado |
| Aviso "no es un abogado" | `POST /cases/{id}/chat` (campo `disclaimer`) | Conectado |
| Generar/editar/descargar derecho de petición o tutela | — | Aún no existe endpoint en el backend; el frontend sigue mostrando datos de ejemplo en "Mis documentos" |
| Biblioteca normativa (listado navegable) | — | Aún no existe endpoint; el frontend sigue mostrando datos de ejemplo |

## Arranque con Docker

```bash
cp server/.env.example server/.env   # y completa GEMINI_API_KEY
docker compose up --build
```

- Frontend: http://localhost:5173
- API: http://localhost:8000 (`/health`, `/cases`, `/cases/{id}/chat`)
- Postgres (pgvector): puerto 5433
- MongoDB: puerto 27019

Antes del primer arranque hay que indexar el RAG (una sola vez, o cuando
cambie el PDF fuente) siguiendo los pasos de
[`server/README.md`](server/README.md#puesta-en-marcha).


## Server

Ver [server/README.md](server/README.md) para arquitectura, puesta en marcha
e ingesta del RAG (Postgres/pgvector sobre la Constitución + memoria de
casos en MongoDB).