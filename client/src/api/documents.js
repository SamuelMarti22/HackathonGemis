// Cliente del backend real para "Mis documentos" (ver server/app/routes/documents.py).
// Forma de cada documento: { id, case_id, tipo, titulo, explicacion_mecanismo,
// cuerpo, aceptado, created_at, updated_at }.

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function asJson(res, mensajeError) {
  if (!res.ok) {
    const err = new Error(res.status === 404 ? "no encontrado" : mensajeError);
    err.status = res.status;
    throw err;
  }
  if (res.status === 204) return null;
  return res.json();
}

export async function listDocuments() {
  const res = await fetch(`${API_URL}/documents`);
  return asJson(res, "No se pudieron cargar tus documentos");
}

export async function getDocument(id) {
  const res = await fetch(`${API_URL}/documents/${id}`);
  return asJson(res, "No se pudo cargar el documento");
}

export async function updateDocument(id, changes) {
  const res = await fetch(`${API_URL}/documents/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(changes),
  });
  return asJson(res, "No se pudo guardar el documento");
}

export async function deleteDocument(id) {
  const res = await fetch(`${API_URL}/documents/${id}`, { method: "DELETE" });
  return asJson(res, "No se pudo eliminar el documento");
}

// No hay endpoint de exportación (PDF/DOCX) todavía: se descarga el texto
// plano del borrador directamente en el navegador.
export function downloadDocumentoTexto(documento) {
  const blob = new Blob([documento.cuerpo], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${documento.titulo || "documento"}.txt`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
