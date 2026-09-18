// Mapea "Recomendaciones o pasos a seguir".

export default function Recomendaciones({ pasos }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="mb-3 flex items-center gap-2 font-semibold text-slate-900">
        ✅ Recomendaciones y pasos a seguir
      </h3>
      <ol className="flex flex-col gap-2">
        {pasos.map((paso, index) => (
          <li key={index} className="flex gap-3 text-slate-700">
            <span className="flex h-6 w-6 flex-none items-center justify-center rounded-full bg-blue-100 text-sm font-semibold text-blue-700">
              {index + 1}
            </span>
            <span>{paso}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}
