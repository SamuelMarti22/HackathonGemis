import { useEffect, useState } from "react";
import DocumentCard from "../components/DocumentCard.jsx";
import { listDocuments } from "../api/documents.js";

export default function MisDocumentos() {
  const [documentos, setDocumentos] = useState([]);
  const [estado, setEstado] = useState("cargando"); // cargando | listo | error
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelado = false;
    listDocuments()
      .then((docs) => {
        if (!cancelado) {
          setDocumentos(docs);
          setEstado("listo");
        }
      })
      .catch((err) => {
        if (!cancelado) {
          setError(err.message);
          setEstado("error");
        }
      });
    return () => {
      cancelado = true;
    };
  }, []);

  return (
    <div className="flex h-screen flex-1 flex-col">
      <header className="border-b border-slate-200 bg-white px-8 py-5">
        <h1 className="font-semibold text-slate-900">Mis documentos</h1>
        <p className="text-sm text-slate-500">
          Los documentos preparados desde tus casos, editables y descargables cuando estén
          listos.
        </p>
      </header>

      <div className="flex-1 overflow-y-auto bg-slate-50 px-8 py-8">
        <div className="mx-auto flex max-w-3xl flex-col gap-5">
          {estado === "cargando" && <p className="text-sm text-slate-500">Cargando documentos…</p>}

          {estado === "error" && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              No pude cargar tus documentos: {error}
            </div>
          )}

          {estado === "listo" && documentos.length === 0 && (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
              Todavía no tienes documentos. Cuéntale tu caso a Lexi en{" "}
              <span className="font-semibold text-slate-700">Asistente legal</span> y, si aplica un
              mecanismo de protección, se generará aquí automáticamente.
            </div>
          )}

          {documentos.map((documento) => (
            <DocumentCard key={documento.id} documento={documento} />
          ))}

          {documentos.length > 0 && (
            <div className="flex items-center gap-3 rounded-2xl border border-blue-100 bg-blue-50 px-5 py-4 text-sm text-blue-800">
              <span>🔄</span>
              <p>
                <span className="font-semibold">Revisa antes de presentar:</span> verifica
                nombres, fechas, entidad y hechos. Estos son borradores de orientación.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
