# Tutor Jurídico — server

Backend del tutor jurídico: FastAPI + RAG propio sobre la Constitución
Política de Colombia (Postgres/pgvector) + memoria de conversación por caso
(MongoDB).

## Arquitectura

```
RAG/COLOMBIA-Constitucion.pdf
        │  ingest/parse_constitution.py  (pdftotext -layout → artículos)
        ▼
server/data/articles.json  ──┐
                              │  ingest/ingest.py (embeddings Gemini)
server/data/article_links.json ──┘        │
   (ingest/build_article_links.py)        ▼
                                Postgres + pgvector (article_chunks)
                                           │
                                    app/retrieval.py (similitud coseno)
                                           │
                                     app/rag.py  ──► Gemini (resumen, normas,
                                           │          mecanismo, documento)
                                           │
                          app/routes/cases.py + app/routes/documents.py
                          + app/chat_service.py
                          (casos, mensajes y documentos en MongoDB)
```

**Diseño anti-alucinación** (ver docstring de `app/rag.py`): el modelo sólo
puede citar artículos que aparecen en la lista de candidatos recuperados por
pgvector; si no hay evidencia suficiente, el bot admite que no encontró
norma aplicable. Después de generar, el backend verifica programáticamente
que cada artículo citado esté realmente entre los candidatos — la URL y el
texto mostrados al usuario siempre se toman de la base de datos, nunca de lo
que "dice" el modelo. La misma verificación aplica al borrador del
documento (tutela, derecho de petición, …) que genera `generate_document`:
si cita un artículo no verificado, se descarta por completo.

## Puesta en marcha

1. Copia `.env.example` a `.env` y completa `GEMINI_API_KEY`.
2. Levanta las bases de datos:
   ```
   docker compose up -d postgres mongo
   ```
3. Instala dependencias (o usa el Dockerfile del server):
   ```
   cd server
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. Genera el índice del RAG (una sola vez, o cada vez que cambie el PDF):
   ```
   python -m ingest.parse_constitution      # PDF -> data/articles.json
   python -m ingest.build_article_links     # -> data/article_links.json (URLs oficiales)
   python -m ingest.ingest --reset          # embeddings -> Postgres/pgvector
   ```
5. Arranca la API:
   ```
   uvicorn app.main:app --reload
   ```
   o con Docker: `docker compose up -d --build server`.

## Endpoints

- `GET /health`
- `POST /cases` → `{id, title, created_at}`
- `GET /cases` → lista de casos
- `GET /cases/{case_id}` → caso + mensajes
- `DELETE /cases/{case_id}`
- `POST /cases/{case_id}/chat` `{"mensaje": "..."}` → Server-Sent Events, en orden:
  - `event: resumen` (varios, streaming) — resumen jurídico de la situación
  - `event: normas` (uno) — `{hay_normas_aplicables, normas_aplicables: [{citation, url, por_que_aplica, extracto, ...}], recomendaciones, mecanismo_recomendado: {tipo, nombre, justificacion, articulo_base, articulo_base_url} | null, disclaimer}`
  - `event: documento` (opcional, solo si hay mecanismo aplicable) — el documento ya guardado en Mongo (sin `cuerpo`)
  - `event: error_documento` (opcional) — el documento falló pero el resumen y las normas siguen siendo válidos
  - `event: done`
  - `event: error` (si falla todo el turno)
- `GET /documents` (`?case_id=` opcional) → lista de documentos generados
- `GET /documents/{id}` → documento completo, incluye `cuerpo`
- `PUT /documents/{id}` `{titulo?, cuerpo?, aceptado?}` → edita el documento
- `DELETE /documents/{id}`

## Notas

- El plan gratuito de la API de Gemini limita `embed_content` a ~100
  items/minuto; `ingest/ingest.py` ya reintenta con backoff cuando recibe
  un 429, así que puede tardar unos minutos en correr contra el corpus
  completo (~550 fragmentos).
- `CHAT_MODEL`: los modelos "flash" recién liberados
  (`gemini-flash-latest`, `gemini-3.6-flash`, …) suelen tener solo 20
  requests/día gratis en una key nueva — cada turno con mecanismo
  aplicable hace 3 llamadas de generación (resumen, normas, documento), así
  que se agota rápido. `gemini-3.5-flash-lite` (el default) tiene cuota
  gratuita mucho más generosa.
- `data/article_links.json` apunta a la Secretaría del Senado; si cambia
  su estructura de páginas, vuelve a correr `build_article_links.py`.
