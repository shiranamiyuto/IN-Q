from abc import ABC, abstractmethod


class Translator(ABC):

    @abstractmethod
    def translate_many(
        self,
        texts: list[str],
        source: str,
        target: str,
    ) -> list[str]:
        """
        Translate multiple text strings.

        The returned list must have the same length and order
        as the input list.
        """
        raise NotImplementedError