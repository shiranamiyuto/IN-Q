import json
import os
from pathlib import Path

from dotenv import load_dotenv

from scripts.github_comments import GitHubCommentsAPI
from scripts.pr_comment_manager import sync_translation_comment
from scripts.pr_translator import translate_pull_request
from scripts.translators import create_translator


ROOT = Path(__file__).resolve().parent.parent

BOT_LOGIN = "github-actions[bot]"


def load_pull_request_event() -> dict:
    """
    Load pull request information from the GitHub Actions event payload.
    """

    event_path = os.getenv("GITHUB_EVENT_PATH")

    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH is not configured.")

    with open(event_path, encoding="utf-8") as event_file:
        event = json.load(event_file)

    pull_request = event.get("pull_request")

    if not isinstance(pull_request, dict):
        raise RuntimeError(
            "GitHub event does not contain pull request information."
        )

    return pull_request


def main() -> None:
    load_dotenv(ROOT / ".env")

    pull_request = load_pull_request_event()

    title = pull_request.get("title")
    body = pull_request.get("body")
    issue_number = pull_request.get("number")

    if not isinstance(title, str):
        raise RuntimeError("Pull request title is missing or invalid.")

    if body is not None and not isinstance(body, str):
        raise RuntimeError("Pull request body has an invalid format.")

    if not isinstance(issue_number, int):
        raise RuntimeError("Pull request number is missing or invalid.")

    translator = create_translator()

    translated_pr = translate_pull_request(
        title=title,
        body=body,
        translator=translator,
    )

    api = GitHubCommentsAPI(
        token=os.getenv("GITHUB_TOKEN", ""),
        repository=os.getenv("GITHUB_REPOSITORY", ""),
        api_url=os.getenv(
            "GITHUB_API_URL",
            "https://api.github.com",
        ),
    )

    action = sync_translation_comment(
        api=api,
        issue_number=issue_number,
        translated_pr=translated_pr,
        bot_login=BOT_LOGIN,
    )

    print(f"Pull Request: #{issue_number}")
    print(f"Detected languages: {translated_pr['languages']}")
    print(f"Translated fields: {translated_pr['translated_fields']}")
    print(f"Comment action: {action}")


if __name__ == "__main__":
    main()
