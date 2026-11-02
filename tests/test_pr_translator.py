
import unittest

from scripts.pr_translator import translate_pull_request
from scripts.translators.base import Translator


class MockTranslator(Translator):

    def __init__(self, language_map, translation_map):
        self.language_map = language_map
        self.translation_map = translation_map
        self.detect_calls = []
        self.translate_calls = []

    def detect_language(self, texts):
        self.detect_calls.append(texts)
        return [
            self.language_map[text]
            for text in texts
        ]

    def translate_many(self, texts, source, target):
        self.translate_calls.append({
            "texts": texts,
            "source": source,
            "target": target,
        })

        return [
            self.translation_map[text]
            for text in texts
        ]


class InvalidLanguageCountTranslator(MockTranslator):

    def detect_language(self, texts):
        return ["en"]


class InvalidTranslationCountTranslator(MockTranslator):

    def translate_many(self, texts, source, target):
        return []


class TestTranslatePullRequest(unittest.TestCase):

    def test_english_title_japanese_body(self):
        translator = MockTranslator(
            language_map={
                "Fix initialization bug": "en",
                "初期化の問題を修正しました。": "ja",
            },
            translation_map={
                "Fix initialization bug": "初期化のバグを修正",
            },
        )

        result = translate_pull_request(
            title="Fix initialization bug",
            body="初期化の問題を修正しました。",
            translator=translator,
        )

        self.assertEqual(result["title"], "初期化のバグを修正")
        self.assertEqual(
            result["body"],
            "初期化の問題を修正しました。",
        )
        self.assertEqual(
            result["translated_fields"],
            ["title"],
        )

    def test_japanese_title_english_body(self):
        translator = MockTranslator(
            language_map={
                "初期化の問題を修正": "ja",
                "The error occurs during startup.": "en",
            },
            translation_map={
                "The error occurs during startup.": "起動時にエラーが発生します。",
            },
        )

        result = translate_pull_request(
            title="初期化の問題を修正",
            body="The error occurs during startup.",
            translator=translator,
        )

        self.assertEqual(result["title"], "初期化の問題を修正")
        self.assertEqual(
            result["body"],
            "起動時にエラーが発生します。",
        )
        self.assertEqual(
            result["translated_fields"],
            ["body"],
        )

    def test_both_fields_are_japanese(self):
        translator = MockTranslator(
            language_map={
                "初期化の問題を修正": "ja",
                "初期化の問題を修正しました。": "ja",
            },
            translation_map={},
        )

        result = translate_pull_request(
            title="初期化の問題を修正",
            body="初期化の問題を修正しました。",
            translator=translator,
        )

        self.assertEqual(
            result["translated_fields"],
            [],
        )
        self.assertEqual(translator.translate_calls, [])
        self.assertEqual(
            result["title"],
            "初期化の問題を修正",
        )
        self.assertEqual(
            result["body"],
            "初期化の問題を修正しました。",
        )

    def test_both_fields_are_english(self):
        translator = MockTranslator(
            language_map={
                "Fix initialization bug": "en",
                "The error occurs during startup.": "en",
            },
            translation_map={
                "Fix initialization bug": "初期化のバグを修正",
                "The error occurs during startup.": "起動時にエラーが発生します。",
            },
        )

        result = translate_pull_request(
            title="Fix initialization bug",
            body="The error occurs during startup.",
            translator=translator,
        )

        self.assertEqual(
            result["title"],
            "初期化のバグを修正",
        )
        self.assertEqual(
            result["body"],
            "起動時にエラーが発生します。",
        )
        self.assertEqual(
            result["translated_fields"],
            ["title", "body"],
        )

        self.assertEqual(len(translator.translate_calls), 1)

    def test_mixed_language_title(self):
        title = (
            "初期化の問題を修正しました。"
            "The error occurs during startup."
        )

        translator = MockTranslator(
            language_map={
                title: "mixed",
                "初期化の問題を修正しました。": "ja",
            },
            translation_map={
                title: (
                    "初期化の問題を修正しました。"
                    "起動時にエラーが発生します。"
                ),
            },
        )

        result = translate_pull_request(
            title=title,
            body="初期化の問題を修正しました。",
            translator=translator,
        )

        self.assertEqual(
            result["title"],
            (
                "初期化の問題を修正しました。"
                "起動時にエラーが発生します。"
            ),
        )
        self.assertEqual(
            result["translated_fields"],
            ["title"],
        )

    def test_empty_body(self):
        translator = MockTranslator(
            language_map={
                "Fix initialization bug": "en",
            },
            translation_map={
                "Fix initialization bug": "初期化のバグを修正",
            },
        )

        result = translate_pull_request(
            title="Fix initialization bug",
            body="",
            translator=translator,
        )

        self.assertEqual(
            result["title"],
            "初期化のバグを修正",
        )
        self.assertEqual(result["body"], "")
        self.assertEqual(
            result["languages"]["body"],
            None,
        )
        self.assertEqual(
            result["translated_fields"],
            ["title"],
        )

    def test_unknown_language(self):
        translator = MockTranslator(
            language_map={
                "Some unfamiliar text": "unknown",
            },
            translation_map={
                "Some unfamiliar text": "不明なテキスト",
            },
        )

        result = translate_pull_request(
            title="Some unfamiliar text",
            body=None,
            translator=translator,
        )

        self.assertEqual(
            result["title"],
            "不明なテキスト",
        )
        self.assertIsNone(result["body"])
        self.assertEqual(
            result["translated_fields"],
            ["title"],
        )

    def test_translation_uses_auto_japanese(self):
        translator = MockTranslator(
            language_map={
                "Fix initialization bug": "en",
            },
            translation_map={
                "Fix initialization bug": "初期化のバグを修正",
            },
        )

        translate_pull_request(
            title="Fix initialization bug",
            body=None,
            translator=translator,
        )

        self.assertEqual(
            translator.translate_calls[0]["source"],
            "auto",
        )
        self.assertEqual(
            translator.translate_calls[0]["target"],
            "Japanese",
        )

    def test_both_fields_are_empty(self):
        translator = MockTranslator(
            language_map={},
            translation_map={},
        )

        result = translate_pull_request(
            title="",
            body="",
            translator=translator,
        )

        self.assertEqual(result["title"], "")
        self.assertEqual(result["body"], "")
        self.assertEqual(
            result["languages"],
            {"title": None, "body": None},
        )
        self.assertEqual(result["translated_fields"], [])
        self.assertEqual(translator.detect_calls, [])
        self.assertEqual(translator.translate_calls, [])

    def test_language_detection_count_mismatch(self):
        translator = InvalidLanguageCountTranslator(
            language_map={},
            translation_map={},
        )

        with self.assertRaises(RuntimeError):
            translate_pull_request(
                title="Fix initialization bug",
                body="The error occurs during startup.",
                translator=translator,
            )

    def test_translation_count_mismatch(self):
        translator = InvalidTranslationCountTranslator(
            language_map={
                "Fix initialization bug": "en",
            },
            translation_map={},
        )

        with self.assertRaises(RuntimeError):
            translate_pull_request(
                title="Fix initialization bug",
                body=None,
                translator=translator,
            )

    def test_chinese_title_and_body(self):
        translator = MockTranslator(
            language_map={
                "修复初始化错误": "zh",
                "启动时发生错误。": "zh",
            },
            translation_map={
                "修复初始化错误": "初期化エラーを修正",
                "启动时发生错误。": "起動時にエラーが発生します。",
            },
        )

        result = translate_pull_request(
            title="修复初始化错误",
            body="启动时发生错误。",
            translator=translator,
        )

        self.assertEqual(
            result["title"],
            "初期化エラーを修正",
        )
        self.assertEqual(
            result["body"],
            "起動時にエラーが発生します。",
        )
        self.assertEqual(
            result["translated_fields"],
            ["title", "body"],
        )

if __name__ == "__main__":
    unittest.main()
