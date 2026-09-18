// Mapea "Norma o normativas aplicables", citadas de forma identificable
// con un hipervínculo hacia el texto de la norma.

export default function NormativasAplicables({ normativas }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="mb-3 flex items-center gap-2 font-semibold text-slate-900">
        📚 Normativa aplicable
      </h3>
      <ul className="flex flex-col gap-3">
        {normativas.map((norma) => (
          <li
            key={norma.titulo}
            className="rounded-xl border border-slate-100 bg-slate-50 p-3"
          >
            <a
              href={norma.url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-blue-700 hover:underline"
            >
              {norma.titulo} ↗
            </a>
            <p className="mt-1 text-sm text-slate-600">{norma.descripcion}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
