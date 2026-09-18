import { useState } from "react";
import DisclaimerBanner from "../components/DisclaimerBanner.jsx";
import ResumenCaso from "../components/ResumenCaso.jsx";
import NormativasAplicables from "../components/NormativasAplicables.jsx";
import Recomendaciones from "../components/Recomendaciones.jsx";
import { mockRespuestaCaso } from "../data/mock.js";

// Página "Asistente legal / Nuevo caso".
// Solo mapea las dos vistas (estado inicial y resultado del caso) con
// datos de ejemplo. El envío real a un backend/RAG no está implementado.

export default function AsistenteLegal() {
  const [relato, setRelato] = useState("");
  const [mostrarResultado, setMostrarResultado] = useState(false);
  const [resumenListo, setResumenListo] = useState(false);

  function handleSubmit(event) {
    event.preventDefault();
    if (!relato.trim()) return;
    setResumenListo(false);
    setMostrarResultado(true);
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit(event);
    }
  }

  function handleNuevoCaso() {
    setRelato("");
    setMostrarResultado(false);
    setResumenListo(false);
  }

  return (
    <div className="flex h-screen flex-1 flex-col">
      <header className="border-b border-slate-200 bg-white px-8 py-5">
        <h1 className="font-semibold text-slate-900">Nuevo caso</h1>
        <p className="text-sm text-slate-500">
          Orientación sobre la Constitución Política de Colombia
        </p>
      </header>

      <div className="flex-1 overflow-y-auto bg-slate-50 px-8 py-8">
        {!mostrarResultado ? (
          <div className="mx-auto flex max-w-2xl flex-col items-center gap-6 pt-10 text-center">
            <div className="flex h-28 w-28 items-center justify-center rounded-2xl bg-blue-50 text-6xl">
              🤖
            </div>
            <div>
              <h2 className="text-3xl font-bold text-slate-900">Hola, soy Lexi</h2>
              <p className="mt-2 text-slate-500">
                Puedo ayudarte a entender tus derechos constitucionales y encontrar el
                camino adecuado.
              </p>
            </div>
          </div>
        ) : (
          <div className="mx-auto flex max-w-3xl flex-col gap-5">
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-sm font-medium text-slate-500">Tu caso</p>
              <p className="mt-1 text-slate-800">{relato}</p>
            </div>

            <ResumenCaso
              texto={mockRespuestaCaso.resumen}
              stream
              onComplete={() => setResumenListo(true)}
            />

            {resumenListo && (
              <div className="flex flex-col gap-5 animate-[fadeIn_0.3s_ease-in]">
                <NormativasAplicables normativas={mockRespuestaCaso.normativas} />
                <Recomendaciones pasos={mockRespuestaCaso.recomendaciones} />
                <DisclaimerBanner />

                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={handleNuevoCaso}
                    className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-white"
                  >
                    Empezar un nuevo caso
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <form
        onSubmit={handleSubmit}
        className="mx-8 mb-8 flex flex-col gap-2 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
      >
        <textarea
          value={relato}
          onChange={(event) => setRelato(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Cuéntame qué ocurrió..."
          rows={2}
          className="resize-none border-none text-slate-800 outline-none placeholder:text-slate-400"
        />
        <div className="flex items-center justify-between border-t border-slate-100 pt-2">
          <span className="text-xs text-slate-400">Presiona Enter para enviar</span>
          <button
            type="submit"
            className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-600 text-white hover:bg-blue-700"
          >
            ↑
          </button>
        </div>
      </form>
    </div>
  );
}
