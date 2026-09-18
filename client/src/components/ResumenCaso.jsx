// Mapea el bloque de "Resumen de la situación en términos legales".
// `texto` se va acumulando a medida que llegan los fragmentos reales del
// streaming SSE del backend (event: resumen); `streaming` controla el
// cursor parpadeante mientras el backend sigue enviando texto.

export default function ResumenCaso({ texto, streaming = false }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="mb-2 flex items-center gap-2 font-semibold text-slate-900">
        📝 Resumen de la situación
      </h3>
      <p className="whitespace-pre-line leading-relaxed text-slate-700">
        {texto}
        {streaming && (
          <span className="ml-0.5 inline-block h-4 w-[2px] animate-pulse bg-blue-500 align-middle" />
        )}
      </p>
    </section>
  );
}
