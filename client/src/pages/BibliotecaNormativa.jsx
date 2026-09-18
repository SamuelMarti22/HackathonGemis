import { useState } from "react";
import { mockNormas } from "../data/mock.js";

// Página "Biblioteca normativa": solo mapea buscador + listado de normas
// con hipervínculo a la fuente. La búsqueda es un filtro local sobre el
// mock, no una consulta real al RAG.

export default function BibliotecaNormativa() {
  const [busqueda, setBusqueda] = useState("");

  const normasFiltradas = mockNormas.filter((norma) =>
    norma.titulo.toLowerCase().includes(busqueda.toLowerCase())
  );

  return (
    <div className="flex h-screen flex-1 flex-col">
      <header className="border-b border-slate-200 bg-white px-8 py-5">
        <h1 className="font-semibold text-slate-900">Biblioteca normativa</h1>
        <p className="text-sm text-slate-500">
          Explora las normas que alimentan las respuestas de Lexi.
        </p>
      </header>

      <div className="flex-1 overflow-y-auto bg-slate-50 px-8 py-8">
        <div className="mx-auto flex max-w-3xl flex-col gap-5">
          <input
            value={busqueda}
            onChange={(event) => setBusqueda(event.target.value)}
            placeholder="Buscar norma, ley o decreto..."
            className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-800 shadow-sm outline-none focus:border-blue-400"
          />

          {normasFiltradas.map((norma) => (
            <div
              key={norma.id}
              className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
            >
              <span className="mb-2 inline-block rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                {norma.categoria}
              </span>
              <h3 className="font-semibold text-slate-900">
                <a
                  href={norma.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-700 hover:underline"
                >
                  {norma.titulo} ↗
                </a>
              </h3>
              <p className="mt-1 text-sm text-slate-600">{norma.descripcion}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
