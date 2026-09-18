// Mapea "Norma o normativas aplicables", citadas de forma identificable
// con un hipervínculo hacia el texto de la norma.
// Forma real de cada item (ver server/app/schemas.py -> NormaCitada):
// { citation, tipo, titulo, capitulo, url, por_que_aplica, extracto }

export default function NormativasAplicables({ normativas }) {
  if (!normativas || normativas.length === 0) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="mb-2 flex items-center gap-2 font-semibold text-slate-900">
          📚 Normativa aplicable
        </h3>
        <p className="text-sm text-slate-600">
          No se encontró un artículo de la Constitución que aplique con certeza a este caso.
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="mb-3 flex items-center gap-2 font-semibold text-slate-900">
        📚 Normativa aplicable
      </h3>
      <ul className="flex flex-col gap-3">
        {normativas.map((norma) => (
          <li
            key={`${norma.tipo}-${norma.citation}`}
            className="rounded-xl border border-slate-100 bg-slate-50 p-3"
          >
            {norma.url ? (
              <a
                href={norma.url}
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-blue-700 hover:underline"
              >
                {norma.citation} ↗
              </a>
            ) : (
              <span className="font-medium text-slate-800">{norma.citation}</span>
            )}

            {(norma.titulo || norma.capitulo) && (
              <p className="mt-0.5 text-xs text-slate-500">
                {[norma.titulo, norma.capitulo].filter(Boolean).join(" · ")}
              </p>
            )}

            <p className="mt-1 text-sm text-slate-700">{norma.por_que_aplica}</p>

            {norma.extracto && (
              <p className="mt-2 border-l-2 border-slate-200 pl-3 text-xs italic text-slate-500">
                “{norma.extracto}”
              </p>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
