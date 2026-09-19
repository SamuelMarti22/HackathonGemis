import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getDocument, updateDocument, downloadDocumentoTexto } from "../api/documents.js";
import { mecanismoNombre } from "../lib/mecanismos.js";

export default function EditorDocumento() {
  const { id } = useParams();
  const [documento, setDocumento] = useState(null);
  const [contenido, setContenido] = useState("");
  const [aceptado, setAceptado] = useState(false);
  const [estado, setEstado] = useState("cargando"); // cargando | listo | no-encontrado | error
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelado = false;
    getDocument(id)
      .then((doc) => {
        if (cancelado) return;
        setDocumento(doc);
        setContenido(doc.cuerpo);
        setAceptado(doc.aceptado);
        setEstado("listo");
      })
      .catch((err) => {
        if (cancelado) return;
        setError(err.message);
        setEstado(err.status === 404 ? "no-encontrado" : "error");
      });
    return () => {
      cancelado = true;
    };
  }, [id]);

  async function guardarCambios(cambiosExtra = {}) {
    setGuardando(true);
    setError(null);
    try {
      const actualizado = await updateDocument(id, { cuerpo: contenido, ...cambiosExtra });
      setDocumento(actualizado);
      if ("aceptado" in cambiosExtra) setAceptado(actualizado.aceptado);
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardando(false);
    }
  }

  function handleAceptar(event) {
    const value = event.target.checked;
    setAceptado(value);
    guardarCambios({ aceptado: value });
  }

  if (estado === "cargando") {
    return (
      <div className="flex h-screen flex-1 items-center justify-center text-slate-500">
        Cargando documento…
      </div>
    );
  }

  if (estado === "no-encontrado" || estado === "error") {
    return (
      <div className="flex h-screen flex-1 flex-col items-center justify-center gap-3 text-slate-500">
        <p>{estado === "no-encontrado" ? "Documento no encontrado." : `No pude cargar el documento: ${error}`}</p>
        <Link to="/documentos" className="text-sm text-blue-600 hover:underline">
          ← Volver a Mis documentos
        </Link>
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
          <p className="text-sm text-slate-500">{mecanismoNombre(documento.tipo)}</p>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
          {aceptado ? "Aceptado" : "Borrador"}
        </span>
      </header>

      <div className="flex-1 overflow-y-auto bg-slate-50 px-8 py-8">
        <div className="mx-auto flex max-w-3xl flex-col gap-5">
          {documento.explicacion_mecanismo && (
            <section className="rounded-2xl border border-blue-100 bg-blue-50/60 p-5 text-sm text-slate-700 shadow-sm">
              {documento.explicacion_mecanismo}
            </section>
          )}

          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              No pude guardar: {error}
            </div>
          )}

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
            <input type="checkbox" checked={aceptado} onChange={handleAceptar} className="h-4 w-4" />
            He revisado el contenido y acepto este documento tal como está.
          </label>

          <div className="flex justify-end gap-3">
            <button
              type="button"
              disabled={guardando}
              onClick={() => guardarCambios()}
              className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-white disabled:opacity-50"
            >
              {guardando ? "Guardando…" : "Guardar borrador"}
            </button>
            <button
              type="button"
              disabled={!aceptado}
              onClick={() => downloadDocumentoTexto({ ...documento, cuerpo: contenido })}
              className="flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              ⬇️ Descargar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
