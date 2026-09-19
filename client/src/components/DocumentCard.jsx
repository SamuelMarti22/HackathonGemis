import { Link } from "react-router-dom";
import { mecanismoNombre } from "../lib/mecanismos.js";
import { downloadDocumentoTexto } from "../api/documents.js";

function formatFecha(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString("es-CO", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  } catch {
    return "";
  }
}

export default function DocumentCard({ documento }) {
  const estado = documento.aceptado ? "Aceptado" : "Borrador";
  const estadoStyle = documento.aceptado
    ? "bg-emerald-50 text-emerald-700"
    : "bg-slate-100 text-slate-600";

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-start gap-4">
        <div className="flex h-11 w-11 flex-none items-center justify-center rounded-xl bg-blue-50 text-xl text-blue-600">
          📄
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-slate-900">{documento.titulo}</h3>
          <p className="text-sm text-slate-500">
            {mecanismoNombre(documento.tipo)} · Editado el {formatFecha(documento.updated_at)}
          </p>
          <span className={`mt-2 inline-block rounded-full px-3 py-1 text-xs font-medium ${estadoStyle}`}>
            {estado}
          </span>
        </div>
      </div>

      <hr className="my-4 border-slate-100" />

      <div className="flex gap-3">
        <Link
          to={`/documentos/${documento.id}/editar`}
          className="rounded-xl bg-blue-50 px-4 py-2 text-sm font-semibold text-blue-700 hover:bg-blue-100"
        >
          Abrir y editar
        </Link>
        <button
          type="button"
          disabled={!documento.aceptado}
          onClick={() => downloadDocumentoTexto(documento)}
          title={documento.aceptado ? undefined : "Acepta el documento en el editor para poder descargarlo"}
          className="flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          ⬇️ Descargar
        </button>
      </div>
    </div>
  );
}
