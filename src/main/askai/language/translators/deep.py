#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.language.argos_translator
      @file: argos_translator.py
   @created: Fri, 5 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.exception.exceptions import MissingApiKeyError
from askai.language.ai_translator import AITranslator
from askai.language.language import Language
from functools import lru_cache

import deepl
import os


class DeepLTranslator(AITranslator):
    """Provides a multilingual online translation engine."""

    def __init__(self, from_idiom: Language, to_idiom: Language):
        super().__init__(from_idiom, to_idiom)
        if not (auth_key := os.environ.get("DEEPL_API_KEY")):
            raise MissingApiKeyError("ApiKey: 'DEEPL_API_KEY' is required to use DeepL translator!")
        self._translator = deepl.Translator(auth_key)

    @lru_cache(maxsize=256)
    def translate(self, text: str) -> str:
        """Translate text using te default translator.
        :param text: Text to translate.
        """
        if self._from_idiom == self._to_idiom:
            return text
        lang = self._from_locale()
        result: deepl.TextResult = self._translator.translate_text(
            text, preserve_formatting=True, source_lang=lang[0], target_lang=lang[1]
        )
        return str(result)

    def name(self) -> str:
        return "DeepL"

    def _from_locale(self) -> tuple[str, ...]:
        """Convert from locale string to DeepL language.
        Ref:.https://developers.deepl.com/docs/resources/supported-languages
        """
        from_lang: str = self._from_idiom.language.upper()
        match self._to_idiom:
            case Language.PT_BR:
                to_lang: str = "PT-BR"
            case Language.PT_PT:
                to_lang: str = "PT-PT"
            case Language.EN_GB:
                to_lang: str = "EN-GB"
            case _:
                if self._to_idiom.language.casefold() == "en":
                    to_lang: str = "en_US"
                elif self._to_idiom.language.casefold() == "zh":
                    to_lang: str = "ZH-HANS"
                else:
                    to_lang: str = self._to_idiom.language.upper()
        return from_lang, to_lang.upper()


if __name__ == "__main__":
    t = DeepLTranslator(Language.EN_US, Language.PT_BR)
    print(t.translate("--- \n Hello \"initialization\"\n How ARE you doing 'what is up'?"))
