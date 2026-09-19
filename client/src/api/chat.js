// Cliente del backend real (FastAPI). Reemplaza los datos mock por las
// llamadas a los endpoints descritos en server/README.md.

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function createCase() {
  const res = await fetch(`${API_URL}/cases`, { method: "POST" });
  if (!res.ok) throw new Error("No se pudo crear el caso");
  return res.json(); // { id, title, created_at }
}

// Consume el streaming SSE de POST /cases/{id}/chat:
//   event: resumen         (varios, texto plano acumulable)
//   event: normas          (uno, JSON: RespuestaJuridica — puede traer mecanismo_recomendado)
//   event: documento       (uno, opcional, JSON: documento guardado en Mongo, sin `cuerpo`)
//   event: error_documento (uno, opcional, JSON: { detail } — no genera el documento pero el
//                            resto del turno sigue siendo válido)
//   event: done
//   event: error           (JSON: { detail } — falla todo el turno)
export async function streamChat(
  caseId,
  mensaje,
  { onResumen, onNormas, onDocumento, onErrorDocumento, onDone, onError }
) {
  let res;
  try {
    res = await fetch(`${API_URL}/cases/${caseId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mensaje }),
    });
  } catch (err) {
    onError?.(err);
    return;
  }

  if (!res.ok || !res.body) {
    onError?.(new Error(`El asistente respondió con un error (${res.status})`));
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let sepIndex;
      while ((sepIndex = buffer.indexOf("\n\n")) !== -1) {
        const rawEvent = buffer.slice(0, sepIndex);
        buffer = buffer.slice(sepIndex + 2);
        dispatchEvent(parseEventBlock(rawEvent), {
          onResumen,
          onNormas,
          onDocumento,
          onErrorDocumento,
          onDone,
          onError,
        });
      }
    }
  } catch (err) {
    onError?.(err);
  }
}

function parseEventBlock(block) {
  let event = "message";
  const dataLines = [];
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).replace(/^ /, ""));
  }
  return { event, data: dataLines.join("\n") };
}

function dispatchEvent(
  { event, data },
  { onResumen, onNormas, onDocumento, onErrorDocumento, onDone, onError }
) {
  if (event === "resumen") {
    onResumen?.(data);
  } else if (event === "normas") {
    onNormas?.(safeJson(data));
  } else if (event === "documento") {
    onDocumento?.(safeJson(data));
  } else if (event === "error_documento") {
    onErrorDocumento?.(new Error(safeJson(data)?.detail || "No se pudo generar el documento"));
  } else if (event === "done") {
    onDone?.();
  } else if (event === "error") {
    onError?.(new Error(safeJson(data)?.detail || "Ocurrió un error en el asistente"));
  }
}

function safeJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}
