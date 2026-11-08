import unittest
from unittest.mock import patch

from scripts.github_comments import GitHubCommentsAPI


class TestGitHubCommentsAPI(unittest.TestCase):

    def setUp(self):
        self.api = GitHubCommentsAPI(
            token="test-token",
            repository="owner/repo",
        )

    def test_list_comments_pagination(self):
        first_page = [
            {"id": i}
            for i in range(100)
        ]

        second_page = [
            {"id": 100},
        ]

        with patch.object(
            self.api,
            "_request",
            side_effect=[first_page, second_page],
        ) as request:

            result = self.api.list_comments(42)

        self.assertEqual(len(result), 101)
        self.assertEqual(request.call_count, 2)

        self.assertIn("page=1", request.call_args_list[0].args[1])
        self.assertIn("page=2", request.call_args_list[1].args[1])

    def test_create_comment(self):
        with patch.object(
            self.api,
            "_request",
            return_value={"id": 123},
        ) as request:

            result = self.api.create_comment(
                42,
                "Translation",
            )

        self.assertEqual(result["id"], 123)

        args = request.call_args

        self.assertEqual(args.args[0], "POST")
        self.assertIn("/issues/42/comments", args.args[1])
        self.assertEqual(
            args.args[2],
            {"body": "Translation"},
        )

    def test_update_comment(self):
        with patch.object(
            self.api,
            "_request",
            return_value={"id": 123},
        ) as request:

            result = self.api.update_comment(
                123,
                "Updated translation",
            )

        self.assertEqual(result["id"], 123)

        args = request.call_args

        self.assertEqual(args.args[0], "PATCH")
        self.assertIn("/issues/comments/123", args.args[1])
        self.assertEqual(
            args.args[2],
            {"body": "Updated translation"},
        )

    def test_delete_comment(self):
        with patch.object(
            self.api,
            "_request",
            return_value=None,
        ) as request:

            self.api.delete_comment(123)

        args = request.call_args

        self.assertEqual(args.args[0], "DELETE")
        self.assertIn("/issues/comments/123", args.args[1])

    def test_missing_token(self):
        with self.assertRaises(ValueError):
            GitHubCommentsAPI(
                token="",
                repository="owner/repo",
            )

    def test_invalid_repository(self):
        with self.assertRaises(ValueError):
            GitHubCommentsAPI(
                token="test-token",
                repository="invalid-repository",
            )


if __name__ == "__main__":
    unittest.main()
