import { useEffect, useRef, useState } from "react";

// Efecto visual de "máquina de escribir" para simular streaming en el
// frontend. Sigue siendo texto mock revelado progresivamente: el día que
// haya streaming real desde el backend, este hook se reemplaza por el
// consumo directo del stream (SSE/fetch stream) token a token.
export default function useTypewriter(text, speed = 15) {
  const [displayedText, setDisplayedText] = useState("");
  const [isDone, setIsDone] = useState(false);
  const indexRef = useRef(0);

  useEffect(() => {
    setDisplayedText("");
    setIsDone(false);
    indexRef.current = 0;

    if (!text) {
      setIsDone(true);
      return;
    }

    const intervalId = setInterval(() => {
      indexRef.current += 1;
      setDisplayedText(text.slice(0, indexRef.current));

      if (indexRef.current >= text.length) {
        clearInterval(intervalId);
        setIsDone(true);
      }
    }, speed);

    return () => clearInterval(intervalId);
  }, [text, speed]);

  return { displayedText, isDone };
}
