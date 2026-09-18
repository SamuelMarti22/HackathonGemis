const DEFAULT_TEXT =
  "Esta herramienta ofrece orientación general y no reemplaza el consejo de un profesional " +
  "del derecho. Verifica siempre la información con un abogado antes de tomar decisiones legales.";

export default function DisclaimerBanner({ texto }) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
      <span className="text-lg leading-none">⚠️</span>
      <p>
        <span className="font-semibold">Lexi no es un abogado.</span> {texto ?? DEFAULT_TEXT}
      </p>
    </div>
  );
}
