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

from argostranslate import package, translate
from argostranslate.translate import ITranslation
from askai.exception.exceptions import TranslationPackageError
from askai.language.ai_translator import AITranslator
from askai.language.language import Language
from functools import lru_cache
from typing import Optional

import logging as log
import os
import sys


class ArgosTranslator(AITranslator):
    """Provides a multilingual offline translation engine.
    Language packages are downloaded at: ~/.local/share/argos-translate/packages
    """

    @staticmethod
    def _get_argos_model(source: Language, target: Language) -> Optional[ITranslation]:
        """Retrieve ARGOS model from source to target languages.
        :param source: The source language.
        :param target: The target language.
        """
        lang = f"{source.name} -> {target.name}"
        log.debug(f"Translating from: {source} to: {target}")
        source_lang = [
            model for model in translate.get_installed_languages() if lang in map(repr, model.translations_from)
        ]
        target_lang = [
            model for model in translate.get_installed_languages() if lang in map(repr, model.translations_to)
        ]
        if len(source_lang) <= 0 or len(target_lang) <= 0:
            log.info('Translation "%s" is not installed!')
            return None

        return source_lang[0].get_translation(target_lang[0])

    def __init__(self, from_idiom: Language, to_idiom: Language):
        super().__init__(from_idiom, to_idiom)
        if argos_model := self._get_argos_model(from_idiom, to_idiom):
            log.debug(f"Argos translator found for: {from_idiom.language} -> {to_idiom.language}")
        elif not self._install_translator():
            raise TranslationPackageError(
                f"Could not install Argos translator: {from_idiom.language} -> {to_idiom.language}"
            )
        else:
            argos_model = self._get_argos_model(from_idiom, to_idiom)
        self._argos_model = argos_model

    @lru_cache(maxsize=256)
    def translate(self, text: str) -> str:
        """Translate text using Argos translator.
        :param text: Text to translate.
        """
        return text if self._from_idiom == self._to_idiom else self._argos_model.translate(text)

    def name(self) -> str:
        return "Argos"

    def _install_translator(self) -> bool:
        """Install the Argos translator if it's not yet installed on the system."""
        old_stdout = sys.stdout
        with open(os.devnull, "w") as dev_null:
            sys.stdout = dev_null
            package.update_package_index()
            required_package = next(
                filter(
                    lambda x: x.from_code == self._from_idiom.language and x.to_code == self._to_idiom.language,
                    package.get_available_packages(),
                )
            )
            log.debug("Downloading and installing translator package: %s", required_package)
            package.install_from_path(required_package.download())
            sys.stdout = old_stdout
        return required_package is not None


if __name__ == "__main__":
    t = ArgosTranslator(Language.EN_US, Language.PT_BR)
    print(t.translate("Hello \"initialization\" how ARE you doing 'what is up'"))
