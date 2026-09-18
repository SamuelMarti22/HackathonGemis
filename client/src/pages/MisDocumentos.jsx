import DocumentCard from "../components/DocumentCard.jsx";
import { mockDocumentos } from "../data/mock.js";

export default function MisDocumentos() {
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
          {mockDocumentos.map((documento) => (
            <DocumentCard key={documento.id} documento={documento} />
          ))}

          <div className="flex items-center gap-3 rounded-2xl border border-blue-100 bg-blue-50 px-5 py-4 text-sm text-blue-800">
            <span>🔄</span>
            <p>
              <span className="font-semibold">Revisa antes de presentar:</span> verifica
              nombres, fechas, entidad y hechos. Estos son borradores de orientación.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
