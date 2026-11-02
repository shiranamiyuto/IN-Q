
from typing import Any

from scripts.translators.base import Translator


TARGET_LANGUAGE = "Japanese"


def translate_pull_request(
    title: str,
    body: str | None,
    translator: Translator,
) -> dict[str, Any]:
    """
    Detect and translate a pull request's title and body.

    Japanese content is preserved.
    Non-Japanese, mixed, and unknown content is translated
    into Japanese using automatic source-language detection.
    """

    fields = {
        "title": title,
        "body": body,
    }

    # Only detect non-empty fields.
    fields_to_detect = {
        name: value
        for name, value in fields.items()
        if value and value.strip()
    }

    languages = {
        "title": None,
        "body": None,
    }

    if fields_to_detect:
        detected_languages = translator.detect_language(
            list(fields_to_detect.values())
        )

        if len(detected_languages) != len(fields_to_detect):
            raise RuntimeError(
                "Language detection count does not match input count."
            )

        languages.update(
            zip(fields_to_detect.keys(), detected_languages)
        )

    # Select fields that are not entirely Japanese.
    fields_to_translate = {
        name: fields[name]
        for name, language in languages.items()
        if language is not None and language != "ja"
    }

    translated_fields = []

    if fields_to_translate:
        translations = translator.translate_many(
            list(fields_to_translate.values()),
            source="auto",
            target=TARGET_LANGUAGE,
        )

        if len(translations) != len(fields_to_translate):
            raise RuntimeError(
                "Translation count does not match input count."
            )

        for name, translation in zip(
            fields_to_translate.keys(),
            translations,
        ):
            fields[name] = translation
            translated_fields.append(name)

    return {
        "title": fields["title"],
        "body": fields["body"],
        "languages": languages,
        "translated_fields": translated_fields,
    }
