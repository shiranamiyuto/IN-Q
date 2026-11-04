import unittest
from unittest.mock import Mock

from scripts import sync_documents


class TestLocalizeReadmeLinks(unittest.TestCase):

    def test_english_links(self):
        text = (
            "[Bug Report](https://github.com/shiranamiyuto/IN-Q/"
            "issues/new?template=bug-report-ja.yml)\n"
            "[Privacy Policy](PRIVACY.md)"
        )

        result = sync_documents.localize_readme_links(text, "en")

        self.assertIn("template=bug-report-en.yml", result)
        self.assertIn("[Privacy Policy](../PRIVACY.md)", result)

    def test_chinese_links(self):
        text = (
            "[不具合報告](https://github.com/shiranamiyuto/IN-Q/"
            "issues/new?template=bug-report-ja.yml)\n"
            "[隐私政策](PRIVACY.md)"
        )

        result = sync_documents.localize_readme_links(text, "zh")

        self.assertIn("template=bug-report-cn.yml", result)
        self.assertIn("[隐私政策](../PRIVACY.md)", result)

    def test_unsupported_language(self):
        with self.assertRaises(ValueError):
            sync_documents.localize_readme_links("README", "ja")


class TestProtectText(unittest.TestCase):

    def test_protect_markdown_content(self):
        source = (
            "# IN-Q V2\n\n"
            "Download from https://example.com\n\n"
            "`some_code()`\n"
        )

        protected, items = sync_documents.protect_text(source)

        self.assertNotEqual(source, protected)
        self.assertIn("ZXQKEEP", protected)
        self.assertGreater(len(items), 0)

    def test_restore_text(self):
        source = "See `some_code()` for details."

        protected_text, items = sync_documents.protect_text(source)
        restored = sync_documents.restore_text(protected_text, items)

        self.assertEqual(restored, source)

    def test_missing_placeholder_fails(self):
        _, items = sync_documents.protect_text("Use `some_code()`.")

        with self.assertRaises(ValueError):
            sync_documents.restore_text("Placeholder removed.", items)

    def test_duplicate_placeholder_fails(self):
        _, items = sync_documents.protect_text("Use `some_code()`.")

        placeholder = next(iter(items))

        with self.assertRaises(ValueError):
            sync_documents.restore_text(
                f"{placeholder} {placeholder}",
                items,
            )

    def test_reordered_placeholders_fail(self):
        _, items = sync_documents.protect_text("`first()` and `second()`.")

        placeholders = list(items)

        reversed_text = (
            placeholders[1] + " " + placeholders[0]
        )

        with self.assertRaises(ValueError):
            sync_documents.restore_text(reversed_text, items)


class TestLanguageSwitch(unittest.TestCase):

    def test_add_english_language_switch(self):
        source = "# IN-Q V2\n\nEnglish content.\n"

        result = sync_documents.add_language_switch(source, "en")

        self.assertIn(
            "[English](README.en.md)",
            result,
        )
        self.assertIn(
            "[日本語](../README.md)",
            result,
        )

        self.assertLess(
            result.index("# IN-Q V2"),
            result.index("[English]"),
        )

    def test_add_chinese_language_switch(self):
        source = "# IN-Q V2\n\n中文内容。\n"

        result = sync_documents.add_language_switch(source, "zh")

        self.assertIn(
            "[简体中文](README.cn.md)",
            result,
        )

    def test_missing_heading_fails(self):
        with self.assertRaises(ValueError):
            sync_documents.add_language_switch(
                "Document without heading.",
                "en",
            )


class TestMarkdownStructure(unittest.TestCase):

    def test_same_structure_passes(self):
        source = (
            "# Japanese title\n\n"
            "- First item\n"
            "- Second item\n"
        )

        target = (
            "# English title\n\n"
            "- First translation\n"
            "- Second translation\n"
        )

        sync_documents.validate_markdown_structure(source, target)

    def test_changed_structure_fails(self):
        source = (
            "# Japanese title\n\n"
            "- First item\n"
        )

        target = (
            "# English title\n\n"
            "First translation\n"
        )

        with self.assertRaises(ValueError):
            sync_documents.validate_markdown_structure(source, target)


class TestTranslateDocument(unittest.TestCase):

    def test_successful_translation(self):
        source = (
            "# IN-Q V2\n\n"
            "ダウンロードしてください。\n"
        )

        translator = Mock()

        def translate(texts, source, target):
            return [
                texts[0].replace(
                    "ダウンロードしてください。",
                    "Please download the application.",
                )
            ]

        translator.translate_many.side_effect = translate
        translator.detect_language.return_value = ["en"]

        result = sync_documents.translate_document(
            source=source,
            translator=translator,
            target_language="English",
            target_language_code="en",
        )

        self.assertIn(
            "Please download the application.",
            result,
        )

        self.assertIn("# IN-Q V2", result)

    def test_wrong_language_fails(self):
        source = "# IN-Q V2\n\n日本語の文章です。\n"

        translator = Mock()
        translator.translate_many.side_effect = (
            lambda texts, source, target: texts
        )
        translator.detect_language.return_value = ["ja"]

        with self.assertRaises(ValueError):
            sync_documents.translate_document(
                source=source,
                translator=translator,
                target_language="English",
                target_language_code="en",
            )

    def test_unknown_language_is_allowed(self):
        source = "# IN-Q V2\n\nShort text.\n"

        translator = Mock()
        translator.translate_many.side_effect = (
            lambda texts, source, target: texts
        )
        translator.detect_language.return_value = ["unknown"]

        result = sync_documents.translate_document(
            source=source,
            translator=translator,
            target_language="English",
            target_language_code="en",
        )

        self.assertIn("Short text.", result)

    def test_translation_localizes_english_links(self):
        source = (
            "# IN-Q V2\n\n"
            "[不具合報告フォーム]("
            "https://github.com/shiranamiyuto/IN-Q/"
            "issues/new?template=bug-report-ja.yml)\n\n"
            "診断情報については[PRIVACY.md](PRIVACY.md)"
            "を参照してください。\n"
        )

        translator = Mock()

        translator.translate_many.side_effect = (
            lambda texts, source, target: [
                texts[0]
                .replace("不具合報告フォーム", "Bug Report Form")
                .replace("診断情報については", "For diagnostic information, see ")
                .replace("を参照してください。", ".")
            ]
        )

        translator.detect_language.return_value = ["en"]

        result = sync_documents.translate_document(
            source=source,
            translator=translator,
            target_language="English",
            target_language_code="en",
        )

        self.assertIn("template=bug-report-en.yml", result)
        self.assertIn("[PRIVACY.md](../PRIVACY.md)", result)

    def test_translation_localizes_chinese_links(self):
        source = (
            "[Bug Report](https://github.com/shiranamiyuto/IN-Q/"
            "issues/new?template=bug-report-ja.yml)\n"
            "[Privacy Policy](PRIVACY.md)"
        )

        translator = Mock()

        translator.translate_many.side_effect = (
            lambda texts, source, target: [texts[0]]
        )

        translator.detect_language.return_value = ["zh"]

        result = sync_documents.translate_document(
            source=source,
            translator=translator,
            target_language="Simplified Chinese",
            target_language_code="zh",
        )

        self.assertIn("bug-report-cn.yml", result)
        self.assertIn("../PRIVACY.md", result)


if __name__ == "__main__":
    unittest.main()
