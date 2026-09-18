import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { mockDocumentos, mockDocumentoContenido } from "../data/mock.js";

// Mapea el flujo "generar derecho de petición / tutela": el usuario
// revisa y edita el contenido, lo acepta y luego puede descargarlo.
// La generación real y el export a PDF no están implementados.

export default function EditorDocumento() {
  const { id } = useParams();
  const documento = mockDocumentos.find((doc) => doc.id === id);
  const [contenido, setContenido] = useState(mockDocumentoContenido[id] ?? "");
  const [aceptado, setAceptado] = useState(false);

  if (!documento) {
    return (
      <div className="flex h-screen flex-1 items-center justify-center text-slate-500">
        Documento no encontrado.
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-1 flex-col">
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-8 py-5">
        <div>
          <Link to="/documentos" className="text-sm text-blue-600 hover:underline">
            ← Mis documentos
          </Link>
          <h1 className="mt-1 font-semibold text-slate-900">{documento.titulo}</h1>
          <p className="text-sm text-slate-500">{documento.tipo}</p>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
          {documento.estado}
        </span>
      </header>

      <div className="flex-1 overflow-y-auto bg-slate-50 px-8 py-8">
        <div className="mx-auto flex max-w-3xl flex-col gap-5">
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="mb-3 font-semibold text-slate-900">Edita el documento</h3>
            <textarea
              value={contenido}
              onChange={(event) => setContenido(event.target.value)}
              rows={16}
              className="w-full resize-none rounded-xl border border-slate-200 p-4 font-mono text-sm text-slate-800 outline-none focus:border-blue-400"
            />
          </section>

          <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700 shadow-sm">
            <input
              type="checkbox"
              checked={aceptado}
              onChange={(event) => setAceptado(event.target.checked)}
              className="h-4 w-4"
            />
            He revisado el contenido y acepto este documento tal como está.
          </label>

          <div className="flex justify-end gap-3">
            <button
              type="button"
              className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-white"
            >
              Guardar borrador
            </button>
            <button
              type="button"
              disabled={!aceptado}
              className="flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              ⬇️ Descargar PDF
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
