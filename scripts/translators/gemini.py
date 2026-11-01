import json
import os

from google import genai
from google.genai import types

from .base import Translator


class GeminiTranslator(Translator):

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable is missing."
            )

        if not model:
            raise RuntimeError(
                "GEMINI_MODEL environment variable is missing."
            )

        self.client = genai.Client(api_key=api_key)
        self.model = model

    def translate_many(
        self,
        texts: list[str],
        source: str,
        target: str,
    ) -> list[str]:

        if not texts:
            return []

        payload = {
            "texts": texts
        }

        prompt = f"""
You are a professional Japanese-to-{target} translator.

Translate the input strings from {source} to {target}.

Context:
- The project is a tool related to Monster Hunter: World Iceborne.
- Some text may contain game terminology.
- Preserve the meaning and context of the original text.
- Use natural language appropriate for a GitHub issue form.

Rules:
1. Translate every input string.
2. Preserve the original order.
3. Return exactly the same number of strings.
4. Do not add explanations or comments.
5. Preserve Markdown formatting and line breaks.
6. Do not modify placeholders such as ZXQKEEP0001QXZ.
7. Do not translate technical identifiers or code.
8. Return valid JSON only.
9. The output must have exactly this JSON structure:
   {{
     "translations": [
       "translated string 1",
       "translated string 2"
     ]
   }}

Input JSON:
{json.dumps(payload, ensure_ascii=False)}
"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        try:
            result = json.loads(response.text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Gemini returned invalid JSON."
            ) from exc

        translations = result.get("translations")

        if not isinstance(translations, list):
            raise RuntimeError(
                "Gemini response is missing 'translations'."
            )

        if len(translations) != len(texts):
            raise RuntimeError(
                "Translation count does not match input count."
            )

        if not all(isinstance(item, str) for item in translations):
            raise RuntimeError(
                "Translation results must all be strings."
            )

        return translations