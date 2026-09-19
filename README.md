# ⚖️ Lexi — Tutor jurídico constitucional

**Lexi** es un tutor jurídico conversacional: la persona cuenta su caso en
lenguaje natural y recibe, en segundos, una lectura en términos legales de
su situación, los artículos de la **Constitución Política de Colombia**
que realmente aplican (citados y con enlace a la fuente oficial), el
mecanismo de protección ciudadana más adecuado (tutela, derecho de
petición, acción de cumplimiento…) y un borrador del documento listo para
editar y descargar.

Todo está **grounded** en un RAG propio sobre la Constitución: el modelo
nunca cita un artículo que no exista, y si no encuentra una norma
aplicable, lo dice explícitamente en vez de inventar una.

> ⚠️ Lexi es una herramienta de orientación educativa. No reemplaza a un
> abogado ni constituye asesoría legal formal.

---

## Índice

- [Funcionalidades](#funcionalidades)
- [Cómo funciona (arquitectura)](#cómo-funciona-arquitectura)
- [El diseño anti-alucinación](#el-diseño-anti-alucinación)
- [Stack técnico](#stack-técnico)
- [Requisitos previos](#requisitos-previos)
- [Dependencias del proyecto](#dependencias-del-proyecto)
- [Arranque rápido con Docker](#-arranque-rápido-con-docker-recomendado)
- [Configuración (variables de entorno)](#configuración-variables-de-entorno)
- [Desarrollo local sin Docker](#desarrollo-local-sin-docker)
- [Indexar el RAG](#indexar-el-rag)
- [Referencia de la API](#referencia-de-la-api)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Límites conocidos y próximos pasos](#límites-conocidos-y-próximos-pasos)

---

## Funcionalidades

**Asistente legal (chat)**
- La persona describe su caso en lenguaje natural.
- 📝 **Resumen jurídico de la situación**, mostrado en *streaming* token a
  token.
- 📚 **Normativa aplicable**: artículos de la Constitución citados de forma
  identificable (`Artículo 86`, `Artículo transitorio 5`, …), cada uno con
  hipervínculo a su texto oficial en la Secretaría del Senado y con la
  explicación de por qué aplica al caso.
- ✅ **Recomendaciones**: pasos concretos y accionables.
- 🛡️ **Mecanismo de protección ciudadana recomendado**: Lexi siempre
  identifica cuál de estos mecanismos es el más adecuado para el caso —
  acción de tutela, derecho de petición, acción de cumplimiento, acción
  popular, habeas corpus o habeas data — y explica por qué.
- ⚠️ Aviso permanente de que la herramienta no sustituye a un abogado.
- 🧠 Memoria de conversación: cada caso recuerda los mensajes anteriores
  para dar seguimiento a la misma situación.

**Mis documentos**
- A partir del mecanismo recomendado, Lexi redacta un **borrador completo**
  del documento correspondiente (encabezado, hechos, fundamentos de
  derecho citando *solo* artículos verificados, petición, placeholders
  para datos personales) y lo guarda automáticamente.
- El usuario puede **editarlo**, **aceptarlo** y **descargarlo**.

## Cómo funciona (arquitectura)

```mermaid
flowchart LR
    subgraph Ingesta [Ingesta del RAG · una sola vez]
        PDF["RAG/COLOMBIA-Constitucion.pdf"] --> Parse["ingest/parse_constitution.py\npdftotext -layout → artículos"]
        Parse --> Links["ingest/build_article_links.py\nURLs oficiales (Senado)"]
        Links --> Embed["ingest/ingest.py\nembeddings (Gemini)"]
    end

    Embed --> PG[(Postgres + pgvector\narticle_chunks)]

    subgraph Turno [Un turno de chat]
        User(["Persona"]) -->|"cuenta su caso"| API["FastAPI\nPOST /cases/ID/chat"]
        API --> Retrieval["retrieval.py\nsimilitud coseno"]
        Retrieval --> PG
        API --> RAG["rag.py\nresumen · normas · mecanismo · documento"]
        RAG -->|"Gemini"| LLM(["Gemini 3.5 Flash-Lite"])
        API --> Mongo[(MongoDB\ncasos · mensajes · documentos)]
        API -->|"SSE: resumen, normas, documento, done"| Client["React (Vite)"]
    end
```

- **`RAG/`** — la fuente: el PDF oficial de la Constitución.
- **`server/`** — FastAPI. Dos bases de datos con roles distintos:
  - **Postgres + pgvector**: el índice vectorial de los artículos (búsqueda
    semántica).
  - **MongoDB**: memoria de conversación (casos, mensajes) y los
    documentos generados.
- **`client/`** — React + Vite + Tailwind: el chat, "Mis documentos" y la
  biblioteca normativa.

## El diseño anti-alucinación

Este es el corazón del proyecto — nunca se le muestra al usuario una norma
o un documento legal que el modelo se haya inventado:

1. **Recuperación con umbral**: se buscan los artículos más parecidos al
   caso en pgvector. Si ni el más parecido supera un umbral mínimo de
   similitud, Lexi responde directamente que no encontró una norma
   aplicable — nunca le pide al modelo que "se las arregle" sin contexto.
2. **Lista cerrada de candidatos**: el modelo solo puede citar un artículo
   si su número aparece *literalmente* en la lista de candidatos que se le
   da en el prompt.
3. **Verificación programática**: después de generar, el backend descarta
   cualquier cita que no esté exactamente entre los candidatos recuperados.
   La URL y el texto que ve el usuario **siempre** se toman de la base de
   datos, nunca de lo que "dice" el modelo — así, aunque alucinara un
   número, jamás llegaría a mostrarse como real.
4. **Mismo criterio para los documentos generados**: el borrador de la
   tutela / derecho de petición / etc. solo puede citar los artículos ya
   verificados en el paso anterior. Si el texto generado menciona un
   artículo no verificado, el documento se descarta por completo en vez de
   entregarse.

Ver el docstring de [`server/app/rag.py`](server/app/rag.py) para el
detalle de implementación.

## Stack técnico

| Capa | Tecnología |
| --- | --- |
| Frontend | React 18 + Vite + Tailwind CSS + React Router |
| Backend | FastAPI (Python) |
| LLM / embeddings | Google Gemini (`google-genai`) |
| Búsqueda vectorial | PostgreSQL + [pgvector](https://github.com/pgvector/pgvector) |
| Memoria de conversación y documentos | MongoDB |
| ORM | SQLAlchemy 2 |
| Contenedores | Docker + Docker Compose |

## Requisitos previos

Para correr todo con Docker (la forma recomendada) solo necesitas:

- [Docker](https://docs.docker.com/get-docker/) y Docker Compose (v2, el
  que trae `docker compose`, no `docker-compose`).
- Una **API key de Gemini** ([Google AI Studio](https://aistudio.google.com/apikey)).
  Al crearla, elige **"Create API key in new project"**: si reutilizas un
  proyecto ya usado por otra key, heredas su cuota diaria ya consumida.

Para desarrollo local sin Docker, además:

- **Python 3.12+**
- **Node.js 20+** y npm
- `poppler-utils` (trae el comando `pdftotext`, usado para parsear el PDF)
  — `apt install poppler-utils` / `pacman -S poppler` / `brew install poppler`
- Un Postgres con la extensión `pgvector` y un MongoDB accesibles (pueden
  ser los del `docker-compose.yml`, sin levantar `server`/`client`)

## Dependencias del proyecto

### Python (`server/requirements.txt`)

```text
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
psycopg[binary]==3.2.3
pgvector==0.3.6
google-genai==1.2.0
pydantic==2.10.4
pydantic-settings==2.7.1
python-dotenv==1.0.1
pymongo>=4.7
```

Instalar con:

```bash
cd server
pip install -r requirements.txt
```

### JavaScript (`client/package.json`)

El ecosistema Node no usa un `requirements.txt`; su equivalente es
`package.json` + `package-lock.json` (ya versionados en el repo). Estas son
las dependencias declaradas:

```json
"dependencies": {
  "react": "^18.3.1",
  "react-dom": "^18.3.1",
  "react-router-dom": "^6.26.0"
},
"devDependencies": {
  "@vitejs/plugin-react": "^4.3.1",
  "autoprefixer": "^10.4.20",
  "postcss": "^8.4.45",
  "tailwindcss": "^3.4.10",
  "vite": "^5.4.2"
}
```

Instalar con:

```bash
cd client
npm install
```

## 🚀 Arranque rápido con Docker (recomendado)

```bash
# 1. Clona el repo y entra a la carpeta
git clone <url-del-repo> && cd HackathonGemis

# 2. Configura tu API key de Gemini
cp server/.env.example server/.env
#   → edita server/.env y pon tu GEMINI_API_KEY

# 3. También en la raíz del proyecto (docker compose la lee de ahí):
echo "GEMINI_API_KEY=tu_api_key_aqui" > .env

# 4. Levanta las bases de datos primero
docker compose up -d postgres mongo

# 5. Indexa el RAG (una sola vez — tarda unos minutos, ver más abajo)
cd server
python -m venv .venv && source .venv/bin/activate  # o el equivalente en tu SO
pip install -r requirements.txt
python -m ingest.parse_constitution
python -m ingest.build_article_links
python -m ingest.ingest --reset
cd ..

# 6. Levanta todo (server + client, ya con el índice listo)
docker compose up -d --build
```

Y listo:

| Servicio | URL |
| --- | --- |
| 🖥️ Frontend | http://localhost:5173 |
| ⚙️ API | http://localhost:8000 (`/health`, `/cases`, `/documents`, docs interactivos en `/docs`) |
| 🐘 Postgres (pgvector) | `localhost:5433` |
| 🍃 MongoDB | `localhost:27019` |

> La ingesta (paso 5) solo hace falta la primera vez, o cuando cambie el
> PDF fuente — no es parte del arranque normal de la app.

## Configuración (variables de entorno)

`server/.env` (a partir de `server/.env.example`):

| Variable | Para qué | Valor por defecto |
| --- | --- | --- |
| `GEMINI_API_KEY` | API key de Gemini (**requerida**) | — |
| `CHAT_MODEL` | Modelo de chat/generación | `gemini-3.5-flash-lite` |
| `EMBEDDING_MODEL` | Modelo de embeddings | `gemini-embedding-001` |
| `EMBEDDING_DIM` | Dimensión de los embeddings guardados | `768` |
| `RETRIEVAL_TOP_K` | Cuántos artículos candidatos se recuperan por consulta | `6` |
| `MIN_SIMILARITY` | Similitud mínima para considerar que sí hay norma aplicable | `0.55` |
| `DATABASE_URL` | Conexión a Postgres (pgvector) | `postgresql+psycopg://postgres:postgres@localhost:5433/tutor_juridico` |
| `MONGO_URI` / `MONGO_DB` | Conexión a MongoDB | `mongodb://localhost:27019` / `tutor_juridico` |

> 💡 **Sobre `CHAT_MODEL`**: los modelos "flash" recién liberados
> (`gemini-flash-latest`, `gemini-3.6-flash`, …) suelen tener solo **20
> requests/día** gratis en una key nueva. `gemini-3.5-flash-lite` tiene una
> cuota gratuita mucho más generosa y buena calidad para este caso de uso.

`client` lee `VITE_API_URL` (por defecto `http://localhost:8000`,
configurado en `docker-compose.yml`).

## Desarrollo local sin Docker

**Backend**

```bash
cd server
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # completa GEMINI_API_KEY y las URLs de tus BD
uvicorn app.main:app --reload
```

**Frontend**

```bash
cd client
npm install
VITE_API_URL=http://localhost:8000 npm run dev
```

## Indexar el RAG

El índice vectorial se construye en tres pasos, cada uno independiente y
re-ejecutable (ver [`server/README.md`](server/README.md) para el detalle):

```bash
cd server
python -m ingest.parse_constitution      # PDF -> data/articles.json (380 artículos + 67 transitorios)
python -m ingest.build_article_links     # -> data/article_links.json (URLs oficiales, Secretaría del Senado)
python -m ingest.ingest --reset          # genera embeddings y llena Postgres/pgvector
```

`ingest.ingest` reintenta automáticamente con backoff si la API de Gemini
responde con límite de cuota (`429`), así que puede tardar varios minutos
en correr contra el corpus completo (~550 fragmentos). Se puede interrumpir
y retomar sin perder lo ya indexado.

## Referencia de la API

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/health` | Estado del servicio |
| `POST` | `/cases` | Crea un caso nuevo → `{id, title, created_at}` |
| `GET` | `/cases` | Lista los casos |
| `GET` | `/cases/{id}` | Caso + historial de mensajes |
| `DELETE` | `/cases/{id}` | Elimina un caso y sus mensajes |
| `POST` | `/cases/{id}/chat` | Envía un mensaje del caso (ver eventos SSE abajo) |
| `GET` | `/documents` | Lista los documentos generados (`?case_id=` para filtrar por caso) |
| `GET` | `/documents/{id}` | Un documento completo (incluye `cuerpo`) |
| `PUT` | `/documents/{id}` | Edita `titulo`, `cuerpo` y/o `aceptado` |
| `DELETE` | `/documents/{id}` | Elimina un documento |

### `POST /cases/{id}/chat`

```json
{ "mensaje": "Mi arrendador cambió la cerradura sin avisarme" }
```

Responde con **Server-Sent Events**, en este orden:

| Evento | Cuándo | Payload |
| --- | --- | --- |
| `resumen` | varias veces, en streaming | fragmento de texto plano |
| `normas` | una vez | `RespuestaJuridica`: `hay_normas_aplicables`, `normas_aplicables[]` (cada una con `citation`, `url`, `por_que_aplica`, `extracto`…), `recomendaciones[]`, `mecanismo_recomendado` (o `null`), `disclaimer` |
| `documento` | solo si hay mecanismo aplicable | documento guardado en Mongo (sin `cuerpo`, para no duplicar payload) |
| `error_documento` | solo si el documento no se pudo generar | `{detail}` — el resto del turno (resumen, normas) sigue siendo válido |
| `done` | al final | `{}` |
| `error` | si algo falla en el turno completo | `{detail}` |

## Estructura del proyecto

```
HackathonGemis/
├── RAG/
│   └── COLOMBIA-Constitucion.pdf       # fuente del RAG
├── client/                             # React + Vite + Tailwind
│   └── src/
│       ├── api/                        # clientes fetch/SSE hacia el backend
│       ├── components/                 # tarjetas de resumen, normas, documentos…
│       └── pages/                      # Asistente legal, Mis documentos, Editor…
├── server/                             # FastAPI
│   ├── app/
│   │   ├── rag.py                      # orquestación del RAG (anti-alucinación)
│   │   ├── retrieval.py                # búsqueda por similitud en pgvector
│   │   ├── chat_service.py             # une memoria (Mongo) + RAG + Gemini
│   │   ├── memory/                     # repositorios Mongo (casos, mensajes, documentos)
│   │   └── routes/                     # endpoints FastAPI
│   ├── ingest/                         # pipeline de indexación del RAG
│   └── data/                           # artefactos generados por la ingesta (versionados)
├── docker-compose.yml
└── README.md                           # este archivo
```

## Límites conocidos y próximos pasos

- **Cuota de Gemini**: el tier gratuito impone límites diarios estrictos
  por modelo. `gemini-3.5-flash-lite` es la opción con mejor cuota
  probada hasta ahora; si escala el uso, conviene habilitar billing.
- **Exportación de documentos**: por ahora la descarga es texto plano
  (`.txt`); falta un endpoint de exportación a PDF/DOCX.
- **Biblioteca normativa**: la página existe en el frontend pero todavía
  muestra datos de ejemplo; no tiene endpoint propio en el backend.
- **Disposiciones transitorias**: los 380 artículos principales de la
  Constitución están 100% indexados; un puñado de disposiciones
  transitorias finales pueden quedar fuera si la ingesta se interrumpió —
  re-correr `ingest.ingest --reset` las completa.
