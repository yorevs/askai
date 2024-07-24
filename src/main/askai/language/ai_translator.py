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
from abc import ABC
from askai.language.language import Language


class AITranslator(ABC):
    """Provides a base class for multilingual offline translation engines. Various implementations can be used."""

    def __init__(self, from_idiom: Language, to_idiom: Language):
        self._from_idiom: Language = from_idiom
        self._to_idiom: Language = to_idiom

    def translate(self, text: str) -> str:
        """Translate text using te default translator.
        :param text: Text to translate.
        """
        ...

    def name(self) -> str:
        """Return the translator name or model."""
        ...
