import json
import logging
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv

from scripts.github_comments import GitHubCommentsAPI
from scripts.pr_comment_manager import sync_translation_comment
from scripts.pr_translator import translate_pull_request
from scripts.translators import create_translator


logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent

BOT_LOGIN = "github-actions[bot]"


def get_github_config() -> dict[str, str]:
    token = os.getenv("GITHUB_TOKEN")
    repository = os.getenv("GITHUB_REPOSITORY")
    api_url = os.getenv(
        "GITHUB_API_URL",
        "https://api.github.com",
    )

    if not token:
        raise RuntimeError("GITHUB_TOKEN is not configured.")

    if not repository:
        raise RuntimeError("GITHUB_REPOSITORY is not configured.")

    return {
        "token": token,
        "repository": repository,
        "api_url": api_url,
    }


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


def get_current_pull_request(
    token: str,
    repository: str,
    pull_request_number: int,
    api_url: str,
) -> dict:
    url = (
        f"{api_url}/repos/"
        f"{repository}/pulls/{pull_request_number}"
    )

    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "IN-Q-PR-Translator",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    except HTTPError as error:
        response_body = error.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            "Failed to fetch current pull request: "
            f"HTTP {error.code}: {response_body}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            f"Failed to connect to GitHub API: {error}"
        ) from error


def is_stale_pull_request_event(
    token: str,
    repository: str,
    pull_request_number: int,
    event_title: str,
    event_body: str,
    api_url: str,
) -> bool:
    current_pr = get_current_pull_request(
        token=token,
        repository=repository,
        pull_request_number=pull_request_number,
        api_url=api_url,
    )

    current_title = current_pr.get("title") or ""
    current_body = current_pr.get("body") or ""

    if (
        current_title != event_title
        or current_body != event_body
    ):
        logger.info(
            "PR has changed since this event was triggered. "
            "Skipping stale event."
        )

        logger.debug("Event title: %r", event_title)
        logger.debug("Current title: %r", current_title)

        logger.debug("Event body: %r", event_body)
        logger.debug("Current body: %r", current_body)

        return True

    return False


def main() -> None:
    load_dotenv(ROOT / ".env")

    github_config = get_github_config()

    pull_request = load_pull_request_event()

    title = pull_request.get("title")
    body = pull_request.get("body")
    issue_number = pull_request.get("number")

    if not isinstance(title, str):
        raise RuntimeError("Pull request title is missing or invalid.")

    if body is None:
        body = ""
    elif not isinstance(body, str):
        raise RuntimeError("Pull request body has an invalid format.")

    if not isinstance(issue_number, int):
        raise RuntimeError("Pull request number is missing or invalid.")

    translator = create_translator()

    translated_pr = translate_pull_request(
        title=title,
        body=body,
        translator=translator,
    )

    if is_stale_pull_request_event(
        token=github_config["token"],
        repository=github_config["repository"],
        pull_request_number=issue_number,
        event_title=title,
        event_body=body,
        api_url=github_config["api_url"],
    ):
        return

    api = GitHubCommentsAPI(
        token=github_config["token"],
        repository=github_config["repository"],
        api_url=github_config["api_url"],
    )

    action = sync_translation_comment(
        api=api,
        issue_number=issue_number,
        translated_pr=translated_pr,
        bot_login=BOT_LOGIN,
    )

    logger.info("Pull Request: #%s", issue_number)
    logger.info(
        "Detected languages: %s",
        translated_pr["languages"],
    )
    logger.info(
        "Translated fields: %s",
        translated_pr["translated_fields"],
    )
    logger.info("Comment action: %s", action)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )

    main()
