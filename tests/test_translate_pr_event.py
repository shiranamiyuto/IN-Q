import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from scripts import translate_pr_event


class TestLoadPullRequestEvent(unittest.TestCase):

    def test_load_pull_request_event(self):
        event = {
            "action": "opened",
            "pull_request": {
                "number": 42,
                "title": "Fix initialization error",
                "body": "The application fails during startup.",
            },
        }

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            delete=False,
        ) as event_file:
            json.dump(event, event_file)
            event_path = event_file.name

        try:
            with patch.dict(
                os.environ,
                {"GITHUB_EVENT_PATH": event_path},
            ):
                result = translate_pr_event.load_pull_request_event()

            self.assertEqual(result, event["pull_request"])

        finally:
            os.unlink(event_path)

    def test_missing_event_path(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                RuntimeError,
                "GITHUB_EVENT_PATH",
            ):
                translate_pr_event.load_pull_request_event()

    def test_missing_pull_request(self):
        event = {"action": "opened"}

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            delete=False,
        ) as event_file:
            json.dump(event, event_file)
            event_path = event_file.name

        try:
            with patch.dict(
                os.environ,
                {"GITHUB_EVENT_PATH": event_path},
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "pull request information",
                ):
                    translate_pr_event.load_pull_request_event()

        finally:
            os.unlink(event_path)


class TestMain(unittest.TestCase):

    @patch("scripts.translate_pr_event.sync_translation_comment")
    @patch("scripts.translate_pr_event.GitHubCommentsAPI")
    @patch("scripts.translate_pr_event.translate_pull_request")
    @patch("scripts.translate_pr_event.create_translator")
    @patch("scripts.translate_pr_event.load_pull_request_event")
    @patch("scripts.translate_pr_event.load_dotenv")
    def test_main(
        self,
        mock_load_dotenv,
        mock_load_event,
        mock_create_translator,
        mock_translate,
        mock_api_class,
        mock_sync_comment,
    ):
        mock_load_event.return_value = {
            "number": 42,
            "title": "Fix initialization error",
            "body": "The application fails during startup.",
        }

        translator = Mock()
        mock_create_translator.return_value = translator

        translated_pr = {
            "title": "初期化エラーを修正",
            "body": "起動時にアプリケーションが失敗します。",
            "languages": {
                "title": "en",
                "body": "en",
            },
            "translated_fields": ["title", "body"],
        }
        mock_translate.return_value = translated_pr

        api = Mock()
        mock_api_class.return_value = api

        mock_sync_comment.return_value = "create"

        with patch.dict(
            os.environ,
            {
                "GITHUB_TOKEN": "test-token",
                "GITHUB_REPOSITORY": "owner/repo",
            },
        ):
            translate_pr_event.main()

        mock_load_dotenv.assert_called_once()

        mock_create_translator.assert_called_once_with()

        mock_translate.assert_called_once_with(
            title="Fix initialization error",
            body="The application fails during startup.",
            translator=translator,
        )

        mock_api_class.assert_called_once_with(
            token="test-token",
            repository="owner/repo",
            api_url="https://api.github.com",
        )

        mock_sync_comment.assert_called_once_with(
            api=api,
            issue_number=42,
            translated_pr=translated_pr,
            bot_login="github-actions[bot]",
        )


if __name__ == "__main__":
    unittest.main()
