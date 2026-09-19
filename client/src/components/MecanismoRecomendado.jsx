import { Link } from "react-router-dom";
import { mecanismoNombre } from "../lib/mecanismos.js";

// Muestra el mecanismo de protección ciudadana que el backend identificó
// como el más adecuado (viene en el evento SSE `normas`, campo
// `mecanismo_recomendado`), y el estado del documento que se genera para
// ese mecanismo (evento `documento`, o `error_documento` si falló).
export default function MecanismoRecomendado({ mecanismo, documento, generandoDocumento, errorDocumento }) {
  if (!mecanismo) return null;

  return (
    <section className="rounded-2xl border border-blue-100 bg-blue-50/60 p-5 shadow-sm">
      <h3 className="mb-2 flex items-center gap-2 font-semibold text-slate-900">
        🛡️ Mecanismo recomendado: {mecanismoNombre(mecanismo.tipo)}
      </h3>
      <p className="text-sm text-slate-700">{mecanismo.justificacion}</p>
      {mecanismo.articulo_base && (
        <p className="mt-2 text-xs text-slate-500">
          Consagrado en{" "}
          {mecanismo.articulo_base_url ? (
            <a
              href={mecanismo.articulo_base_url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-blue-700 hover:underline"
            >
              {mecanismo.articulo_base} ↗
            </a>
          ) : (
            mecanismo.articulo_base
          )}
        </p>
      )}

      <hr className="my-4 border-blue-100" />

      {documento ? (
        <div className="flex items-center justify-between gap-3 rounded-xl bg-white p-3">
          <div>
            <p className="text-sm font-semibold text-slate-900">📄 {documento.titulo}</p>
            <p className="text-xs text-slate-500">Borrador generado, listo para revisar y editar.</p>
          </div>
          <Link
            to={`/documentos/${documento.id}/editar`}
            className="flex-none rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
          >
            Abrir y editar
          </Link>
        </div>
      ) : errorDocumento ? (
        <p className="text-sm text-amber-700">
          No pude preparar el borrador del documento automáticamente ({errorDocumento.message}). El
          resto de la orientación sigue siendo válida; puedes pedírmelo de nuevo o contarme más
          detalles.
        </p>
      ) : generandoDocumento ? (
        <p className="text-sm text-slate-500">Preparando el borrador del documento…</p>
      ) : null}
    </section>
  );
}
