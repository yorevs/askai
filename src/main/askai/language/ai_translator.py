#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.language.argos_translator
      @file: translator.py
   @created: Fri, 5 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.language.language import Language
from functools import lru_cache
from typing import Protocol


class AITranslator(Protocol):
    """Provides a base class for multilingual offline translation engines. Various implementations can be used."""

    def __init__(self, source_lang: Language, target_lang: Language):
        self._source_lang: Language = source_lang
        self._target_lang: Language = target_lang

    @lru_cache
    def translate(self, text: str, **kwargs) -> str:
        """Translate text from the source language to the target language.
        :param text: Text to translate.
        :return: The translated text.
        """
        ...

    def name(self) -> str:
        """Return the translator name or model.
        :return: The name or model of the translator.
        """
        ...
