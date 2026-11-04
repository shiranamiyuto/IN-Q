import logging
import re
from pathlib import Path

from dotenv import load_dotenv

from scripts.translators import create_translator


logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent

DOCUMENTS = {
    "README": {
        "source": ROOT / "README.md",
        "outputs": {
            "en": ROOT / "readme" / "README.en.md",
            "cn": ROOT / "readme" / "README.cn.md",
        },
    },
    "PRIVACY": {
        "source": ROOT / "PRIVACY.md",
        "outputs": {
            "en": ROOT / "privacy" / "PRIVACY.en.md",
            "cn": ROOT / "privacy" / "PRIVACY.cn.md",
        },
    },
}

LANGUAGES = {
    "en": {
        "name": "English",
        "code": "English",
        "language_code": "en",
        "issue_template": "bug-report-en.yml",
        "privacy_file": "PRIVACY.en.md",
    },
    "cn": {
        "name": "Simplified Chinese",
        "code": "Simplified Chinese",
        "language_code": "zh",
        "issue_template": "bug-report-cn.yml",
        "privacy_file": "PRIVACY.cn.md",
    },
}


def is_supported_language(language: str) -> bool:
    """Check whether a language code is supported."""

    return any(
        config["language_code"] == language
        for config in LANGUAGES.values()
    )


LANGUAGE_SWITCH_PATTERN = re.compile(
    r"^\[日本語\]\([^)]*\)\s*\|\s*"
    r"\[English\]\([^)]*\)\s*\|\s*"
    r"\[简体中文\]\([^)]*\)\s*$",
    re.MULTILINE,
)

# Protect Markdown syntax and content that must remain unchanged.
PROTECTED_PATTERN = re.compile(
    r"```[\s\S]*?```"
    r"|~~~[\s\S]*?~~~"
    r"|<!--[\s\S]*?-->"
    r"|`[^`\n]+`"
    r"|https?://[^\s<>\])]+"
    r"|\]\([^)\n]*\)"
    r"|</?[A-Za-z][^>\n]*>"
    r"|^ {0,3}(?:#{1,6}[ \t]+|[-*+][ \t]+|\d+[.)][ \t]+|>[ \t]?)"
    r"|^[ \t]*(?:[-*_][ \t]*){3,}$"
    r"|(?<!\w)(?:\.{1,2}/)?[\w.-]+(?:/[\w.-]+)+"
    r"|(?<!\w)[\w.-]+\.(?:md|yml|yaml|py|json|txt)\b"
    r"|(?<!\w)(?!IN-Q(?![A-Za-z0-9]))[A-Z][A-Z0-9_-]{1,}(?!\w)"
    r"|\r?\n",
    re.MULTILINE,
)

# Markdown syntax whose presence and order must remain unchanged.
STRUCTURE_PATTERN = re.compile(
    r"^ {0,3}(?:#{1,6}[ \t]+|[-*+][ \t]+|\d+[.)][ \t]+|>[ \t]?)"
    r"|```|~~~"
    r"|`"
    r"|<!--|-->"
    r"|</?[A-Za-z][^>\n]*>"
    r"|\]\([^)\n]*\)",
    re.MULTILINE,
)


ISSUE_FORM_URL = (
    "https://github.com/shiranamiyuto/IN-Q/issues/new?template="
)


def localize_document_links(
    text: str,
    language: str,
    document_name: str,
) -> str:
    """Apply deterministic language-specific document links."""

    if not is_supported_language(language):
        raise ValueError(
            f"Unsupported document language: {language}"
        )

    if document_name == "README":
        language_config = next(
            config
            for config in LANGUAGES.values()
            if config["language_code"] == language
        )

        issue_template = language_config["issue_template"]
        privacy_file = language_config["privacy_file"]

        # Point to the matching language's issue form.
        text = text.replace(
            f"{ISSUE_FORM_URL}bug-report-ja.yml",
            f"{ISSUE_FORM_URL}{issue_template}",
        )

        # Point to the matching language's Privacy Policy.
        text = re.sub(
            r"(\[[^\]]+\]\()PRIVACY\.md(\))",
            rf"\1../privacy/{privacy_file}\2",
            text,
        )

    return text


def remove_language_switch(text: str) -> str:
    """Remove the language switch line before translating the source."""

    text = LANGUAGE_SWITCH_PATTERN.sub("", text, count=1)

    # Normalize excessive blank lines left by removing the switch.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text


def add_language_switch(
    text: str,
    language: str,
    document_name: str = "README",
) -> str:
    """Insert a fixed language switch below the document title."""

    if not is_supported_language(language):
        raise ValueError(f"Unsupported language: {language}")

    switches = {
        "README": (
            "[日本語](../README.md) | "
            "[English](README.en.md) | "
            "[简体中文](README.cn.md)"
        ),
        "PRIVACY": (
            "[日本語](../PRIVACY.md) | "
            "[English](PRIVACY.en.md) | "
            "[简体中文](PRIVACY.cn.md)"
        ),
    }

    if document_name not in switches:
        raise ValueError(f"Unsupported document: {document_name}")

    lines = text.splitlines()

    if not lines or not lines[0].startswith("# "):
        raise ValueError(
            f"{document_name} must start with a level-one heading."
        )

    lines = [
        line for line in lines
        if not LANGUAGE_SWITCH_PATTERN.fullmatch(line)
    ]

    body = "\n".join(lines[1:]).lstrip("\n")

    return (
        lines[0]
        + "\n\n"
        + switches[document_name]
        + "\n\n"
        + body.rstrip()
        + "\n"
    )


def protect_text(text: str):
    """Replace protected Markdown content with unique placeholders."""

    protected = {}
    counter = 0

    def replace(match):
        nonlocal counter

        placeholder = f"ZXQKEEP{counter:04d}QXZ"
        protected[placeholder] = match.group(0)
        counter += 1

        return placeholder

    result = PROTECTED_PATTERN.sub(replace, text)

    return result, protected


def restore_text(text: str, protected: dict):
    """Validate and restore all protected content."""

    positions = []

    for placeholder, original in protected.items():
        count = text.count(placeholder)

        if count != 1:
            logger.warning(
                "Placeholder validation failed: %s "
                "(original=%r, occurrences=%d)",
                placeholder,
                original,
                count,
            )

            logger.debug(
                "Raw translated text:\n%s",
                text,
            )

            raise ValueError(
                f"Placeholder validation failed: {placeholder}"
            )

        positions.append(text.index(placeholder))

    if positions != sorted(positions):
        logger.warning(
            "Protected Markdown content changed its original order."
        )

        raise ValueError(
            "Protected Markdown content changed its original order."
        )

    for placeholder, original in protected.items():
        text = text.replace(placeholder, original)

    return text


def markdown_structure_signature(text: str):
    """Return structural markers and line layout for comparison."""

    return {
        "markers": STRUCTURE_PATTERN.findall(text),
        "line_count": text.count("\n"),
        "blank_lines": len(
            re.findall(r"\n[ \t]*\n", text)
        ),
    }


def validate_markdown_structure(source: str, target: str):
    """Ensure Markdown structure and line layout remain unchanged."""

    if markdown_structure_signature(source) != (
        markdown_structure_signature(target)
    ):
        raise ValueError(
            "Markdown structure differs from the Japanese source."
        )


def validate_translation_language(
    text: str,
    translator,
    expected_language: str,
):
    """Check that the translated document uses the expected language."""

    detected = translator.detect_language([text])

    if len(detected) != 1:
        raise ValueError(
            "Language validation count does not match document count."
        )

    language = detected[0]

    valid_languages = {
        "ja",
        "en",
        "zh",
        "mixed",
        "unknown",
    }

    if language not in valid_languages:
        raise ValueError(
            f"Invalid language detection result: {language}"
        )

    # Unknown is allowed, matching the existing template sync policy.
    if language not in {expected_language, "unknown"}:
        raise ValueError(
            f"Expected {expected_language}, detected {language}."
        )


def translate_document(
    source: str,
    translator,
    target_language: str,
    target_language_code: str,
    document_name: str = "README",
):
    """Translate a Markdown document while preserving its structure."""

    source = remove_language_switch(source)

    protected_text, protected = protect_text(source)

    translations = translator.translate_many(
        texts=[protected_text],
        source="Japanese",
        target=target_language,
    )

    if len(translations) != 1:
        raise ValueError(
            "Unexpected number of translated documents."
        )

    translated = restore_text(translations[0], protected)

    validate_markdown_structure(source, translated)

    translated = localize_document_links(
        text=translated,
        language=target_language_code,
        document_name=document_name,
    )

    validate_translation_language(
        text=translated,
        translator=translator,
        expected_language=target_language_code,
    )

    return translated


def generate_documents(
    source: str,
    translator,
    document_name: str = "README",
):
    """Generate and validate every target before writing any file."""

    generated = {}

    for suffix, language in LANGUAGES.items():
        logger.info(
            "Translating %s to %s...",
            document_name,
            language["name"],
        )

        translated = translate_document(
            source=source,
            translator=translator,
            target_language=language["code"],
            target_language_code=language["language_code"],
            document_name=document_name,
        )

        translated = add_language_switch(
            translated,
            language["language_code"],
            document_name,
        )

        generated[suffix] = translated

        logger.info(
            "Validation passed: %s",
            language["name"],
        )

    return generated


def write_documents(
    generated: dict,
    output_files: dict | None = None,
):
    """Write generated documents after all translations have passed."""

    if output_files is None:
        output_files = DOCUMENTS["README"]["outputs"]

    for suffix, content in generated.items():
        output_file = output_files[suffix]

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file.write_text(
            content,
            encoding="utf-8",
            newline="\n",
        )

        logger.info(
            "Generated: %s",
            output_file.relative_to(ROOT),
        )


def main():
    load_dotenv(ROOT / ".env")

    translator = create_translator()

    # Generate and validate every document before writing any file.
    generated_documents = {}

    for document_name, config in DOCUMENTS.items():
        source_file = config["source"]

        if not source_file.exists():
            raise FileNotFoundError(
                f"Japanese {document_name} not found: {source_file}"
            )

        source = source_file.read_text(encoding="utf-8")

        if not source.strip():
            raise ValueError(
                f"Japanese {document_name} is empty."
            )

        logger.info("")
        logger.info("Source: %s", source_file.name)

        generated_documents[document_name] = generate_documents(
            source=source,
            translator=translator,
            document_name=document_name,
        )

    # Write only after all translations have passed validation.
    for document_name, generated in generated_documents.items():
        write_documents(
            generated=generated,
            output_files=DOCUMENTS[document_name]["outputs"],
        )

    logger.info("")
    logger.info("All document translations generated successfully.")


def localize_readme_links(text: str, language: str) -> str:
    """Backward-compatible README link localization."""

    return localize_document_links(
        text=text,
        language=language,
        document_name="README",
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )

    main()
