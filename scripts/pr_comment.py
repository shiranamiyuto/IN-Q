from typing import Any


COMMENT_MARKER = "<!-- inq-auto-translation -->"

COMMENT_HEADER = "## 日本語訳（自動翻訳）"

COMMENT_TITLE = "### タイトル"

COMMENT_DESCRIPTION = "### 説明"

COMMENT_FOOTER = (
    "英語から日本語への自動翻訳です。"
    "参考情報としてご利用ください。"
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
        COMMENT_TITLE,
        title,
    ]

    if body and body.strip():
        sections.extend([
            "",
            COMMENT_DESCRIPTION,
            body,
        ])

    sections.extend([
        "",
        "---",
        "",
        COMMENT_FOOTER,
    ])

    return "\n".join(sections)
