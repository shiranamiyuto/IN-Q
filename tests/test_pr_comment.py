import unittest

from scripts.pr_comment import (
    COMMENT_FOOTER,
    COMMENT_HEADER,
    COMMENT_MARKER,
    format_translation_comment,
)


class TestFormatTranslationComment(unittest.TestCase):

    def test_title_and_body(self):
        translated_pr = {
            "title": "初期化エラーを修正",
            "body": "起動時にエラーが発生します。",
        }

        result = format_translation_comment(translated_pr)

        self.assertIn(COMMENT_MARKER, result)
        self.assertIn(COMMENT_HEADER, result)
        self.assertIn("### Title", result)
        self.assertIn("初期化エラーを修正", result)
        self.assertIn("### Description", result)
        self.assertIn("起動時にエラーが発生します。", result)
        self.assertIn(COMMENT_FOOTER, result)

    def test_empty_body_none(self):
        translated_pr = {
            "title": "初期化エラーを修正",
            "body": None,
        }

        result = format_translation_comment(translated_pr)

        self.assertIn("初期化エラーを修正", result)
        self.assertNotIn("### Description", result)
        self.assertNotIn("None", result)

    def test_empty_body_string(self):
        translated_pr = {
            "title": "初期化エラーを修正",
            "body": "",
        }

        result = format_translation_comment(translated_pr)

        self.assertIn("初期化エラーを修正", result)
        self.assertNotIn("### Description", result)

    def test_whitespace_body(self):
        translated_pr = {
            "title": "初期化エラーを修正",
            "body": "   \n  ",
        }

        result = format_translation_comment(translated_pr)

        self.assertIn("初期化エラーを修正", result)
        self.assertNotIn("### Description", result)


if __name__ == "__main__":
    unittest.main()
