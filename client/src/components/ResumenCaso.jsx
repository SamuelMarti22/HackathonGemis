import { useEffect, useRef } from "react";
import useTypewriter from "../hooks/useTypewriter.js";

// Mapea el bloque de "Resumen de la situación en términos legales",
// con un efecto de "máquina de escribir" que simula la llegada del
// texto en streaming. `onComplete` avisa a la página cuando terminó,
// para revelar las secciones siguientes (normativa, recomendaciones).

export default function ResumenCaso({ texto, stream = false, onComplete }) {
  const { displayedText, isDone } = useTypewriter(stream ? texto : "", 12);
  const textoAMostrar = stream ? displayedText : texto;
  const mostrandoCursor = stream && !isDone;
  const yaAvisado = useRef(false);

  useEffect(() => {
    if (!stream) return;
    if (isDone && !yaAvisado.current) {
      yaAvisado.current = true;
      onComplete?.();
    }
    if (!isDone) {
      yaAvisado.current = false;
    }
  }, [isDone, stream, onComplete]);

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="mb-2 flex items-center gap-2 font-semibold text-slate-900">
        📝 Resumen de la situación
      </h3>
      <p className="leading-relaxed text-slate-700">
        {textoAMostrar}
        {mostrandoCursor && (
          <span className="ml-0.5 inline-block h-4 w-[2px] animate-pulse bg-blue-500 align-middle" />
        )}
      </p>
    </section>
  );
}
