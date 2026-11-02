import unittest

from unittest.mock import Mock, call

from scripts.pr_comment import COMMENT_MARKER
from scripts.pr_comment_manager import (
    determine_comment_action,
    find_translation_comments,
    sync_translation_comment,
)


BOT_LOGIN = "github-actions[bot]"


def make_comment(
    comment_id: int,
    body: str,
    login: str = BOT_LOGIN,
) -> dict:
    return {
        "id": comment_id,
        "body": body,
        "user": {
            "login": login,
        },
    }


class TestFindTranslationComments(unittest.TestCase):

    def test_find_bot_translation_comment(self):
        comments = [
            make_comment(
                1,
                f"{COMMENT_MARKER}\n日本語訳",
            ),
            make_comment(
                2,
                "普通のコメント",
                login="contributor",
            ),
        ]

        result = find_translation_comments(
            comments,
            BOT_LOGIN,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 1)

    def test_ignore_marker_from_contributor(self):
        comments = [
            make_comment(
                1,
                f"{COMMENT_MARKER}\n日本語訳",
                login="contributor",
            ),
        ]

        result = find_translation_comments(
            comments,
            BOT_LOGIN,
        )

        self.assertEqual(result, [])


class TestDetermineCommentAction(unittest.TestCase):

    def test_create_when_no_existing_comment(self):
        translated_pr = {
            "translated_fields": ["title", "body"],
        }

        result = determine_comment_action(
            translated_pr,
            [],
            BOT_LOGIN,
        )

        self.assertEqual(result["action"], "create")

    def test_update_existing_comment(self):
        translated_pr = {
            "translated_fields": ["title"],
        }

        comments = [
            make_comment(
                123,
                f"{COMMENT_MARKER}\n日本語訳",
            ),
        ]

        result = determine_comment_action(
            translated_pr,
            comments,
            BOT_LOGIN,
        )

        self.assertEqual(result["action"], "update")
        self.assertEqual(result["comment_id"], 123)

    def test_delete_when_translation_is_no_longer_needed(self):
        translated_pr = {
            "translated_fields": [],
        }

        comments = [
            make_comment(
                123,
                f"{COMMENT_MARKER}\n日本語訳",
            ),
        ]

        result = determine_comment_action(
            translated_pr,
            comments,
            BOT_LOGIN,
        )

        self.assertEqual(result["action"], "delete")
        self.assertEqual(
            result["delete_comment_ids"],
            [123],
        )

    def test_none_when_no_translation_and_no_comment(self):
        translated_pr = {
            "translated_fields": [],
        }

        result = determine_comment_action(
            translated_pr,
            [],
            BOT_LOGIN,
        )

        self.assertEqual(result["action"], "none")

    def test_cleanup_duplicate_comments(self):
        translated_pr = {
            "translated_fields": ["body"],
        }

        comments = [
            make_comment(
                123,
                f"{COMMENT_MARKER}\n日本語訳 1",
            ),
            make_comment(
                456,
                f"{COMMENT_MARKER}\n日本語訳 2",
            ),
        ]

        result = determine_comment_action(
            translated_pr,
            comments,
            BOT_LOGIN,
        )

        self.assertEqual(result["action"], "update")
        self.assertEqual(result["comment_id"], 123)
        self.assertEqual(
            result["delete_comment_ids"],
            [456],
        )


class TestSyncTranslationComment(unittest.TestCase):

    def setUp(self):
        self.api = Mock()
        self.issue_number = 42
        self.bot_login = BOT_LOGIN

        self.translated_pr = {
            "title": "初期化エラーを修正",
            "body": "起動時にエラーが発生します。",
            "translated_fields": ["title", "body"],
        }

    def test_create_comment(self):
        self.api.list_comments.return_value = []

        result = sync_translation_comment(
            self.api,
            self.issue_number,
            self.translated_pr,
            self.bot_login,
        )

        self.assertEqual(result, "create")
        self.api.create_comment.assert_called_once()

        args = self.api.create_comment.call_args.args

        self.assertEqual(args[0], self.issue_number)
        self.assertIn(COMMENT_MARKER, args[1])

    def test_update_comment(self):
        self.api.list_comments.return_value = [
            make_comment(
                123,
                f"{COMMENT_MARKER}\n旧翻訳",
            ),
        ]

        result = sync_translation_comment(
            self.api,
            self.issue_number,
            self.translated_pr,
            self.bot_login,
        )

        self.assertEqual(result, "update")
        self.api.update_comment.assert_called_once()

        args = self.api.update_comment.call_args.args

        self.assertEqual(args[0], 123)
        self.assertIn("初期化エラーを修正", args[1])

    def test_delete_comment(self):
        self.api.list_comments.return_value = [
            make_comment(
                123,
                f"{COMMENT_MARKER}\n旧翻訳",
            ),
        ]

        translated_pr = {
            "title": "日本語のタイトル",
            "body": "日本語の説明です。",
            "translated_fields": [],
        }

        result = sync_translation_comment(
            self.api,
            self.issue_number,
            translated_pr,
            self.bot_login,
        )

        self.assertEqual(result, "delete")
        self.api.delete_comment.assert_called_once_with(123)

    def test_no_action(self):
        self.api.list_comments.return_value = []

        translated_pr = {
            "title": "日本語のタイトル",
            "body": "日本語の説明です。",
            "translated_fields": [],
        }

        result = sync_translation_comment(
            self.api,
            self.issue_number,
            translated_pr,
            self.bot_login,
        )

        self.assertEqual(result, "none")
        self.api.create_comment.assert_not_called()
        self.api.update_comment.assert_not_called()
        self.api.delete_comment.assert_not_called()

    def test_update_before_deleting_duplicates(self):
        self.api.list_comments.return_value = [
            make_comment(
                123,
                f"{COMMENT_MARKER}\n旧翻訳 1",
            ),
            make_comment(
                456,
                f"{COMMENT_MARKER}\n旧翻訳 2",
            ),
        ]

        result = sync_translation_comment(
            self.api,
            self.issue_number,
            self.translated_pr,
            self.bot_login,
        )

        self.assertEqual(result, "update")

        self.assertEqual(
            self.api.method_calls,
            [
                call.list_comments(self.issue_number),
                call.update_comment(
                    123,
                    self.api.update_comment.call_args.args[1],
                ),
                call.delete_comment(456),
            ],
        )

    def test_do_not_delete_duplicates_when_update_fails(self):
        self.api.list_comments.return_value = [
            make_comment(
                123,
                f"{COMMENT_MARKER}\n旧翻訳 1",
            ),
            make_comment(
                456,
                f"{COMMENT_MARKER}\n旧翻訳 2",
            ),
        ]

        self.api.update_comment.side_effect = RuntimeError(
            "GitHub API update failed."
        )

        with self.assertRaises(RuntimeError):
            sync_translation_comment(
                self.api,
                self.issue_number,
                self.translated_pr,
                self.bot_login,
            )

        self.api.delete_comment.assert_not_called()


if __name__ == "__main__":
    unittest.main()
