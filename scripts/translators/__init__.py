import os

from .base import Translator
from .gemini import GeminiTranslator


def create_translator() -> Translator:
    # Select the translator implementation configured in .env.
    # To add another provider, implement it and register it here.
    # See base.py for the translator interface.
    provider = os.getenv(
        "TRANSLATOR_PROVIDER",
        "gemini",
    ).lower()

    if provider == "gemini":
        return GeminiTranslator()

    raise ValueError(
        f"Unsupported translator provider: {provider}"
    )