import copy
import os
import re
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import (
    DoubleQuotedScalarString,
    FoldedScalarString,
    LiteralScalarString,
    PlainScalarString,
    SingleQuotedScalarString,
)

from translators import create_translator


ROOT = Path(__file__).resolve().parent.parent

TEMPLATE_DIR = ROOT / ".github" / "ISSUE_TEMPLATE"

SOURCE_FILE = TEMPLATE_DIR / "bug-report-ja.yml"

LANGUAGES = {
    "en": {
        "name": "English",
        "code": "English",
    },
    "cn": {
        "name": "Simplified Chinese",
        "code": "Simplified Chinese",
    },
}

# Protect code blocks, inline code, URLs, and HTML tags.
PROTECTED_PATTERN = re.compile(
    r"```[\s\S]*?```"
    r"|`[^`\n]+`"
    r"|https?://[^\s<>\])]+"
    r"|</?[A-Za-z][^>\n]*>"
)


def load_yaml(path: Path):
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.width = 4096

    with path.open("r", encoding="utf-8") as file:
        return yaml.load(file)


def save_yaml(data, path: Path):
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.width = 4096

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="\n") as file:
        yaml.dump(data, file)


def styled_string(original, value: str):
    """
    Preserve the original YAML scalar style where possible.
    """

    if isinstance(original, LiteralScalarString):
        return LiteralScalarString(value)

    if isinstance(original, FoldedScalarString):
        return FoldedScalarString(value)

    if isinstance(original, DoubleQuotedScalarString):
        return DoubleQuotedScalarString(value)

    if isinstance(original, SingleQuotedScalarString):
        return SingleQuotedScalarString(value)

    if isinstance(original, PlainScalarString):
        return PlainScalarString(value)

    return value


def get_path(data, path):
    current = data

    for key in path:
        current = current[key]

    return current


def set_path(data, path, value):
    current = data

    for key in path[:-1]:
        current = current[key]

    current[path[-1]] = value


def collect_translatable_fields(data):
    """
    Return paths of all user-visible natural-language strings.

    Intentionally excluded:
    - title
    - labels
    - assignees
    - id
    - type
    - validations
    - required
    - render
    """

    paths = []

    for key in ("name", "description"):
        value = data.get(key)

        if isinstance(value, str) and value.strip():
            paths.append((key,))

    for index, item in enumerate(data.get("body", [])):
        attributes = item.get("attributes", {})

        for key in (
            "label",
            "description",
            "placeholder",
            "value",
        ):
            value = attributes.get(key)

            if isinstance(value, str) and value.strip():
                paths.append(
                    ("body", index, "attributes", key)
                )

        options = attributes.get("options", [])

        if item.get("type") == "dropdown":
            for option_index, option in enumerate(options):
                if isinstance(option, str) and option.strip():
                    paths.append(
                        (
                            "body",
                            index,
                            "attributes",
                            "options",
                            option_index,
                        )
                    )

        elif item.get("type") == "checkboxes":
            for option_index, option in enumerate(options):
                if not isinstance(option, dict):
                    continue

                label = option.get("label")

                if isinstance(label, str) and label.strip():
                    paths.append(
                        (
                            "body",
                            index,
                            "attributes",
                            "options",
                            option_index,
                            "label",
                        )
                    )

    return paths


def protect_text(text: str):
    """
    Replace code, URLs, and HTML tags with placeholders.

    The original content is restored after translation.
    """

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
    """
    Verify every placeholder is preserved exactly once.
    """

    for placeholder, original in protected.items():
        count = text.count(placeholder)

        if count != 1:
            raise ValueError(
                f"Placeholder validation failed: {placeholder}"
            )

        text = text.replace(placeholder, original)

    return text


def to_plain(value):
    """
    Convert ruamel YAML containers into ordinary Python containers.
    """

    if isinstance(value, dict):
        return {
            key: to_plain(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            to_plain(item)
            for item in value
        ]

    return value


def normalize_structure(data, paths):
    """
    Replace translated values with a constant before comparison.
    Everything else must remain identical to the Japanese source.
    """

    normalized = copy.deepcopy(data)

    for path in paths:
        set_path(
            normalized,
            path,
            "__TRANSLATED__",
        )

    return to_plain(normalized)


def validate_ids(source, target):
    def extract_ids(data):
        result = []

        for item in data.get("body", []):
            if "id" in item:
                result.append(item["id"])

        return result

    source_ids = extract_ids(source)
    target_ids = extract_ids(target)

    if len(source_ids) != len(set(source_ids)):
        raise ValueError("Duplicate IDs found in source template.")

    if source_ids != target_ids:
        raise ValueError(
            "Field IDs or their order differ from source template."
        )


def validate_template(source, target, paths):
    source_structure = normalize_structure(source, paths)
    target_structure = normalize_structure(target, paths)

    if source_structure != target_structure:
        raise ValueError(
            "Template structure differs from Japanese source."
        )

    validate_ids(source, target)


def translate_template(
    source,
    paths,
    translator,
    target_language,
):
    result = copy.deepcopy(source)

    original_texts = [
        get_path(source, path)
        for path in paths
    ]

    protected_items = [
        protect_text(text)
        for text in original_texts
    ]

    texts_to_translate = [
        item[0]
        for item in protected_items
    ]

    translations = translator.translate_many(
        texts=texts_to_translate,
        source="Japanese",
        target=target_language,
    )

    if len(translations) != len(paths):
        raise ValueError(
            "Unexpected number of translated fields."
        )

    for path, original, translated, protected in zip(
        paths,
        original_texts,
        translations,
        [item[1] for item in protected_items],
    ):
        restored = restore_text(
            translated,
            protected,
        )

        set_path(
            result,
            path,
            styled_string(original, restored),
        )

    return result


def main():
    load_dotenv(ROOT / ".env")

    if not SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"Japanese source template not found: {SOURCE_FILE}"
        )

    source = load_yaml(SOURCE_FILE)

    paths = collect_translatable_fields(source)

    if not paths:
        raise ValueError(
            "No translatable fields found in source template."
        )

    print(f"Source: {SOURCE_FILE.name}")
    print(f"Translatable fields: {len(paths)}")

    translator = create_translator()

    # Generate and validate all targets before writing any files.
    generated = {}

    for suffix, language in LANGUAGES.items():
        print(f"\nTranslating to {language['name']}...")

        translated = translate_template(
            source=source,
            paths=paths,
            translator=translator,
            target_language=language["code"],
        )

        validate_template(
            source=source,
            target=translated,
            paths=paths,
        )

        generated[suffix] = translated

        print(f"Validation passed: {language['name']}")

    # Write files only after every target has passed validation.
    for suffix, translated in generated.items():
        output_file = (
            TEMPLATE_DIR / f"bug-report-{suffix}.yml"
        )

        save_yaml(translated, output_file)

        print(f"Generated: {output_file.relative_to(ROOT)}")

    print("\nAll templates generated successfully.")


if __name__ == "__main__":
    main()