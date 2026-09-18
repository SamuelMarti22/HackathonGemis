import { Link } from "react-router-dom";

const estadoStyles = {
  "Listo para revisar": "bg-emerald-50 text-emerald-700",
  Borrador: "bg-slate-100 text-slate-600",
};

export default function DocumentCard({ documento }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-start gap-4">
        <div className="flex h-11 w-11 flex-none items-center justify-center rounded-xl bg-blue-50 text-xl text-blue-600">
          📄
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-slate-900">{documento.titulo}</h3>
          <p className="text-sm text-slate-500">
            {documento.tipo} · {documento.editado}
          </p>
          <span
            className={`mt-2 inline-block rounded-full px-3 py-1 text-xs font-medium ${
              estadoStyles[documento.estado] ?? "bg-slate-100 text-slate-600"
            }`}
          >
            {documento.estado}
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
          className="flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        >
          ⬇️ Descargar PDF
        </button>
      </div>
    </div>
  );
}
