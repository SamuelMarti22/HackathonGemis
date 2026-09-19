from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.cases import router as cases_router
from app.routes.documents import router as documents_router

app = FastAPI(title="Tutor Jurídico RAG")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases_router)
app.include_router(documents_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
