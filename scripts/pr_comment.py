from typing import Any


COMMENT_MARKER = "<!-- inq-auto-translation -->"

COMMENT_HEADER = "## 日本語訳（自動翻訳）"

COMMENT_FOOTER = (
    "Translated from English to Japanese. "
    "This translation is provided for reference only."
)


def format_translation_comment(
    translated_pr: dict[str, Any],
) -> str:
    """
    Format translated pull request content as a GitHub comment.

    The comment contains a marker used to identify and update
    the bot's existing translation comment.
    """

    title = translated_pr["title"]
    body = translated_pr["body"]

    sections = [
        COMMENT_MARKER,
        COMMENT_HEADER,
        "",
        "### Title",
        title,
    ]

    if body and body.strip():
        sections.extend([
            "",
            "### Description",
            body,
        ])

    sections.extend([
        "",
        "---",
        "",
        COMMENT_FOOTER,
    ])

    return "\n".join(sections)
