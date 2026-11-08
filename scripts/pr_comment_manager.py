from typing import Any

from scripts.pr_comment import COMMENT_MARKER, format_translation_comment


def find_translation_comments(
    comments: list[dict[str, Any]],
    bot_login: str,
) -> list[dict[str, Any]]:
    """
    Find comments created by the expected bot
    that contain the translation marker.
    """

    return [
        comment
        for comment in comments
        if (
            comment.get("user", {}).get("login") == bot_login
            and COMMENT_MARKER in (comment.get("body") or "")
        )
    ]


def determine_comment_action(
    translated_pr: dict[str, Any],
    comments: list[dict[str, Any]],
    bot_login: str,
) -> dict[str, Any]:
    """
    Determine whether to create, update, delete,
    or leave the translation comment unchanged.
    """

    existing_comments = find_translation_comments(
        comments,
        bot_login,
    )

    translated_fields = translated_pr.get(
        "translated_fields",
        [],
    )

    if translated_fields:
        if not existing_comments:
            return {
                "action": "create",
                "comment_id": None,
                "delete_comment_ids": [],
            }

        # Keep the first matching comment and update it.
        primary_comment = existing_comments[0]

        duplicate_comment_ids = [
            comment["id"]
            for comment in existing_comments[1:]
        ]

        return {
            "action": "update",
            "comment_id": primary_comment["id"],
            "delete_comment_ids": duplicate_comment_ids,
        }

    if existing_comments:
        return {
            "action": "delete",
            "comment_id": None,
            "delete_comment_ids": [
                comment["id"]
                for comment in existing_comments
            ],
        }

    return {
        "action": "none",
        "comment_id": None,
        "delete_comment_ids": [],
    }


def sync_translation_comment(
    api,
    issue_number: int,
    translated_pr: dict[str, Any],
    bot_login: str,
) -> str:
    """
    Synchronize the translation comment with the current PR content.

    Returns the action performed: create, update, delete, or none.
    """

    comments = api.list_comments(issue_number)

    decision = determine_comment_action(
        translated_pr,
        comments,
        bot_login,
    )

    action = decision["action"]

    if action == "create":
        body = format_translation_comment(translated_pr)

        api.create_comment(
            issue_number,
            body,
        )

    elif action == "update":
        body = format_translation_comment(translated_pr)

        api.update_comment(
            decision["comment_id"],
            body,
        )

        # Delete duplicates only after the primary update succeeds.
        for comment_id in decision["delete_comment_ids"]:
            api.delete_comment(comment_id)

    elif action == "delete":
        for comment_id in decision["delete_comment_ids"]:
            api.delete_comment(comment_id)

    return action