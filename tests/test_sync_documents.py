import unittest
from unittest.mock import Mock, patch

from scripts import sync_documents


class TestLocalizeReadmeDocumentLinks(unittest.TestCase):
    """Test README-specific link localization."""

    def test_english_links(self):
        text = (
            "[Bug Report](https://github.com/shiranamiyuto/IN-Q/"
            "issues/new?template=bug-report-ja.yml)\n"
            "[Privacy Policy](PRIVACY.md)"
        )

        result = sync_documents.localize_document_links(
            text=text,
            language="en",
            document_name="README",
        )

        self.assertIn("template=bug-report-en.yml", result)
        self.assertIn(
            "[Privacy Policy](../privacy/PRIVACY.en.md)",
            result,
        )

    def test_chinese_links(self):
        text = (
            "[不具合報告](https://github.com/shiranamiyuto/IN-Q/"
            "issues/new?template=bug-report-ja.yml)\n"
            "[隐私政策](PRIVACY.md)"
        )

        result = sync_documents.localize_document_links(
            text=text,
            language="zh",
            document_name="README",
        )

        self.assertIn("template=bug-report-cn.yml", result)
        self.assertIn(
            "[隐私政策](../privacy/PRIVACY.cn.md)",
            result,
        )

    def test_unsupported_language(self):
        with self.assertRaises(ValueError):
            sync_documents.localize_document_links(
                text="README",
                language="ja",
                document_name="README",
            )


class TestLocalizePrivacyLinks(unittest.TestCase):
    """Test that Privacy documents are not processed as READMEs."""

    def test_privacy_links_remain_unchanged(self):
        text = (
            "[Privacy Policy](PRIVACY.md)\n"
            "[Bug Report](https://github.com/shiranamiyuto/"
            "IN-Q/issues/new?template=bug-report-ja.yml)"
        )

        result = sync_documents.localize_document_links(
            text=text,
            language="en",
            document_name="PRIVACY",
        )

        self.assertEqual(result, text)

    def test_unsupported_language(self):
        with self.assertRaises(ValueError):
            sync_documents.localize_document_links(
                text="Privacy Policy",
                language="ja",
                document_name="PRIVACY",
            )


class TestLanguageSwitch(unittest.TestCase):
    """Test README language switch generation."""

    def test_add_english_language_switch(self):
        source = "# IN-Q V2\n\nEnglish content.\n"

        result = sync_documents.add_language_switch(
            source,
            "en",
            "README",
        )

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

        result = sync_documents.add_language_switch(
            source,
            "zh",
            "README",
        )

        self.assertIn(
            "[简体中文](README.cn.md)",
            result,
        )

    def test_missing_heading_fails(self):
        with self.assertRaises(ValueError):
            sync_documents.add_language_switch(
                "Document without heading.",
                "en",
                "README",
            )


class TestPrivacyLanguageSwitch(unittest.TestCase):
    """Test Privacy Policy language switch generation."""

    def test_add_english_language_switch(self):
        result = sync_documents.add_language_switch(
            "# Privacy Policy\n\nContent.",
            "en",
            "PRIVACY",
        )

        self.assertIn(
            "[日本語](../PRIVACY.md)",
            result,
        )
        self.assertIn(
            "[English](PRIVACY.en.md)",
            result,
        )
        self.assertIn(
            "[简体中文](PRIVACY.cn.md)",
            result,
        )

    def test_add_chinese_language_switch(self):
        result = sync_documents.add_language_switch(
            "# 隐私政策\n\n内容。",
            "zh",
            "PRIVACY",
        )

        self.assertIn(
            "[日本語](../PRIVACY.md)",
            result,
        )
        self.assertIn(
            "[English](PRIVACY.en.md)",
            result,
        )
        self.assertIn(
            "[简体中文](PRIVACY.cn.md)",
            result,
        )

    def test_unsupported_document_fails(self):
        with self.assertRaises(ValueError):
            sync_documents.add_language_switch(
                "# Test\n\nContent.",
                "en",
                "UNKNOWN",
            )

    def test_unsupported_language_fails(self):
        with self.assertRaises(ValueError):
            sync_documents.add_language_switch(
                "# 测试\n\n内容。",
                "ja",
                "PRIVACY",
            )


class TestProtectText(unittest.TestCase):
    """Test protection and restoration of Markdown content."""

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


class TestMarkdownStructure(unittest.TestCase):
    """Test Markdown structure validation."""

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
    """Test document translation and its validation pipeline."""

    def test_successful_translation(self):
        source = (
            "# IN-Q V2\n\n"
            "ダウンロードしてください。\n"
        )

        translator = Mock()

        translator.translate_many.side_effect = (
            lambda texts, source, target: [
                texts[0].replace(
                    "ダウンロードしてください。",
                    "Please download the application.",
                )
            ]
        )

        translator.detect_language.return_value = ["en"]

        result = sync_documents.translate_document(
            source=source,
            translator=translator,
            target_language="English",
            target_language_code="en",
            document_name="README",
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
                document_name="README",
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
            document_name="README",
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
                .replace(
                    "診断情報については",
                    "For diagnostic information, see ",
                )
                .replace("を参照してください。", ".")
            ]
        )

        translator.detect_language.return_value = ["en"]

        result = sync_documents.translate_document(
            source=source,
            translator=translator,
            target_language="English",
            target_language_code="en",
            document_name="README",
        )

        self.assertIn("template=bug-report-en.yml", result)
        self.assertIn(
            "[PRIVACY.md](../privacy/PRIVACY.en.md)",
            result,
        )

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
            document_name="README",
        )

        self.assertIn("bug-report-cn.yml", result)
        self.assertIn("../privacy/PRIVACY.cn.md", result)


class TestDocumentConfiguration(unittest.TestCase):
    """Test language configuration and document output paths."""

    def test_privacy_output_paths(self):
        self.assertEqual(
            sync_documents.DOCUMENTS["PRIVACY"]["outputs"]["en"],
            sync_documents.ROOT / "privacy" / "PRIVACY.en.md",
        )
        self.assertEqual(
            sync_documents.DOCUMENTS["PRIVACY"]["outputs"]["cn"],
            sync_documents.ROOT / "privacy" / "PRIVACY.cn.md",
        )

    def test_all_languages_have_required_configuration(self):
        required_keys = {
            "name",
            "code",
            "language_code",
            "issue_template",
            "privacy_file",
        }

        language_codes = []
        issue_templates = []
        privacy_files = []

        for suffix, config in sync_documents.LANGUAGES.items():
            with self.subTest(language=suffix):
                self.assertTrue(required_keys.issubset(config))

                self.assertIn(
                    suffix,
                    sync_documents.DOCUMENTS["README"]["outputs"],
                )
                self.assertIn(
                    suffix,
                    sync_documents.DOCUMENTS["PRIVACY"]["outputs"],
                )

                self.assertEqual(
                    sync_documents.DOCUMENTS["README"]["outputs"][suffix].name,
                    f"README.{suffix}.md",
                )
                self.assertEqual(
                    sync_documents.DOCUMENTS["PRIVACY"]["outputs"][suffix].name,
                    config["privacy_file"],
                )

                language_codes.append(config["language_code"])
                issue_templates.append(config["issue_template"])
                privacy_files.append(config["privacy_file"])

        self.assertEqual(len(language_codes), len(set(language_codes)))
        self.assertEqual(len(issue_templates), len(set(issue_templates)))
        self.assertEqual(len(privacy_files), len(set(privacy_files)))

        configured_languages = set(sync_documents.LANGUAGES)

        self.assertEqual(
            set(sync_documents.DOCUMENTS["README"]["outputs"]),
            configured_languages,
        )
        self.assertEqual(
            set(sync_documents.DOCUMENTS["PRIVACY"]["outputs"]),
            configured_languages,
        )


class TestSelectDocuments(unittest.TestCase):
    """Test document selection."""

    def test_default_selects_all_documents(self):
        result = sync_documents.select_documents()

        self.assertEqual(
            list(result),
            ["README", "PRIVACY"],
        )

    def test_select_readme_only(self):
        result = sync_documents.select_documents(["README"])

        self.assertEqual(
            list(result),
            ["README"],
        )

    def test_select_privacy_only(self):
        result = sync_documents.select_documents(["PRIVACY"])

        self.assertEqual(
            list(result),
            ["PRIVACY"],
        )

    def test_select_both_documents(self):
        result = sync_documents.select_documents(
            ["README", "PRIVACY"]
        )

        self.assertEqual(
            list(result),
            ["README", "PRIVACY"],
        )

    def test_duplicate_document_is_ignored(self):
        result = sync_documents.select_documents(
            ["README", "README"]
        )

        self.assertEqual(
            list(result),
            ["README"],
        )

    def test_empty_selection_fails(self):
        with self.assertRaises(ValueError):
            sync_documents.select_documents([])

    def test_unsupported_document_fails(self):
        with self.assertRaises(ValueError):
            sync_documents.select_documents(["UNKNOWN"])


class TestMain(unittest.TestCase):
    """Test document synchronization entry point."""

    def test_main_translates_only_selected_documents(self):

        source_file = Mock()
        source_file.exists.return_value = True
        source_file.name = "README.md"
        source_file.read_text.return_value = "# README"

        readme_outputs = {
            "en": sync_documents.ROOT / "readme" / "README.en.md",
            "cn": sync_documents.ROOT / "readme" / "README.cn.md",
        }

        documents = {
            "README": {
                "source": source_file,
                "outputs": readme_outputs,
            },
            "PRIVACY": {
                "source": Mock(),
                "outputs": {},
            },
        }

        with (
            patch.dict(sync_documents.DOCUMENTS, documents, clear=True),
            patch("scripts.sync_documents.load_dotenv"),
            patch("scripts.sync_documents.create_translator"),
            patch("scripts.sync_documents.generate_documents") as generate,
            patch("scripts.sync_documents.write_documents") as write,
        ):
            generate.return_value = {
                "en": "English README",
                "cn": "Chinese README",
            }

            sync_documents.main(["README"])

        generate.assert_called_once()
        self.assertEqual(
            generate.call_args.kwargs["document_name"],
            "README",
        )

        write.assert_called_once()
        self.assertEqual(
            write.call_args.kwargs["output_files"],
            readme_outputs,
        )

        source_file.read_text.assert_called_once_with(
            encoding="utf-8"
        )


if __name__ == "__main__":
    unittest.main()
