#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-CFMan
   @package: askai.exception.exceptions
      @file: exceptions.py
   @created: Fri, 12 May 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

from hspylib.core.exception.exceptions import HSBaseException


class NoSuchEngineError(HSBaseException):
    """Raised when the provided engine does not exist"""


class InvalidRecognitionApiError(HSBaseException):
    """Raised when an invalid recognition API callback is provided."""


class IntelligibleAudioError(HSBaseException):
    """Raised when an the provided audio was not recognized by the API."""


class RecognitionApiRequestError(HSBaseException):
    """Raised when an there was an error calling the recognition API."""


class TranslationPackageError(HSBaseException):
    """Raised when an there was an error installing an Argos translation package."""


class TokenLengthExceeded(HSBaseException):
    """Raised when the token is too big to fit the token context window."""


class InvalidInputDevice(HSBaseException):
    """Raised when an invalid recording input device is used."""


class DocumentsNotFound(HSBaseException):
    """Raised when no documents are found for summarization."""


class InaccurateResponse(HSBaseException):
    """Raised when detected an inaccurate response form the AI."""


class MaxInteractionsReached(HSBaseException):
    """Raised when the number of executed actions exceeded the limit."""


class ImpossibleQuery(HSBaseException):
    """Raised when tracing or executing an action plan is/was not possible."""


class TerminatingQuery(HSBaseException):
    """Raised when received a terminating question."""


class InvalidStructuredResponse(HSBaseException):
    """Raised when received an invalid structured response."""


class MissingApiKeyError(HSBaseException):
    """Raised when received an invalid structured response."""


class WebCamInitializationFailure(HSBaseException):
    """Raised when failed to initialize the computer Webcam."""


class CameraAccessFailure(HSBaseException):
    """Raised when failed to operate with the computer Webcam."""


class InterruptionRequest(HSBaseException):
    """Raised when the AI flags to interrupt the execution of the action plan."""
