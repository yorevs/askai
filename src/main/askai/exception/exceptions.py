#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-CFMan
   @package: askai.exception
      @file: exceptions.py
   @created: Fri, 12 May 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""

from hspylib.core.exception.exceptions import HSBaseException


class InvalidRecognitionApiError(HSBaseException):
    """Raised when an invalid recognition API callback is provided."""


class IntelligibleAudioError(HSBaseException):
    """Raised when an the provided audio was not recognized by the API."""


class RecognitionApiRequestError(HSBaseException):
    """Raised when an there was an error calling the recognition API."""


class TranslationPackageError(HSBaseException):
    """Raised when an there was an error installing an Argos translation package."""
