import express from "express";
import cors from "cors";

// Server placeholder: solo define el contrato de la API que el
// frontend ya está mapeando. Ninguna ruta implementa lógica real
// (RAG, generación de documentos, streaming, etc.) todavía.

const app = express();
app.use(cors());
app.use(express.json());

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

// Contrato futuro: analizar un caso en lenguaje natural.
// Debería responder con streaming (resumen legal, normas, recomendaciones).
app.post("/api/casos", (_req, res) => {
  res.status(501).json({ error: "Not implemented" });
});

// Contrato futuro: generar un derecho de petición o tutela a partir de un caso.
app.post("/api/documentos", (_req, res) => {
  res.status(501).json({ error: "Not implemented" });
});

const port = process.env.PORT || 4000;
app.listen(port, () => {
  console.log(`Lexi server (stub) escuchando en el puerto ${port}`);
});
