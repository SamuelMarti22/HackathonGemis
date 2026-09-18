"""Punto de entrada CLI temporal para probar el tutor (luego será la API)."""
from app.config import get_settings
from app.llm import GeminiClient
from app.tutor import LegalTutor


def main() -> None:
    tutor = LegalTutor(GeminiClient(get_settings()))
    case = input("Cuéntame tu caso: ")
    for piece in tutor.answer(case):
        print(piece, end="", flush=True)
    print()


if __name__ == "__main__":
    main()
