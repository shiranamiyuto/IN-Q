from abc import ABC, abstractmethod


class Translator(ABC):

    @abstractmethod
    def detect_language(self, texts: list[str]) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def translate_many(
        self,
        texts: list[str],
        source: str,
        target: str,
    ) -> list[str]:
        """
        Translate multiple text strings.

        Use source="auto" to automatically detect the source language
        and preserve content already written in the target language.

        The returned list must have the same length and order
        as the input list.
        """
        raise NotImplementedError