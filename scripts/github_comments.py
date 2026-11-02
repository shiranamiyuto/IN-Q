import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class GitHubCommentsAPI:

    def __init__(
        self,
        token: str,
        repository: str,
        api_url: str = "https://api.github.com",
    ):
        if not token:
            raise ValueError("GitHub token is required.")

        if not repository or "/" not in repository:
            raise ValueError(
                "Repository must use the owner/repository format."
            )

        self.token = token
        self.repository = repository
        self.api_url = api_url.rstrip("/")

    def _request(
        self,
        method: str,
        path: str,
        payload: dict | None = None,
    ):
        url = f"{self.api_url}{path}"

        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "IN-Q-Multilingual-Support",
        }

        data = None

        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")

        request = Request(
            url,
            data=data,
            headers=headers,
            method=method,
        )

        with urlopen(request, timeout=30) as response:
            response_body = response.read()

        if not response_body:
            return None

        return json.loads(response_body)

    def list_comments(
        self,
        issue_number: int,
    ) -> list[dict]:
        comments = []
        page = 1

        while True:
            query = urlencode({
                "per_page": 100,
                "page": page,
            })

            path = (
                f"/repos/{self.repository}"
                f"/issues/{issue_number}/comments?{query}"
            )

            result = self._request("GET", path)

            if not isinstance(result, list):
                raise RuntimeError(
                    "GitHub returned an invalid comments response."
                )

            comments.extend(result)

            if len(result) < 100:
                break

            page += 1

        return comments

    def create_comment(
        self,
        issue_number: int,
        body: str,
    ) -> dict:
        path = (
            f"/repos/{self.repository}"
            f"/issues/{issue_number}/comments"
        )

        return self._request(
            "POST",
            path,
            {"body": body},
        )

    def update_comment(
        self,
        comment_id: int,
        body: str,
    ) -> dict:
        path = (
            f"/repos/{self.repository}"
            f"/issues/comments/{comment_id}"
        )

        return self._request(
            "PATCH",
            path,
            {"body": body},
        )

    def delete_comment(
        self,
        comment_id: int,
    ) -> None:
        path = (
            f"/repos/{self.repository}"
            f"/issues/comments/{comment_id}"
        )

        self._request("DELETE", path)
