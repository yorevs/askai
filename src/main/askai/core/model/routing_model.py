import os
from typing import Any

from hspylib.core.enums.enumeration import Enumeration
from hspylib.core.preconditions import check_not_none


class RoutingModel(Enumeration):
    """TODO"""

    # fmt: on

    # TERMINAL_COMMAND
    GPT_001 = "TERMINAL_COMMAND", (
        "Select this model for executing shell commands, managing terminal operations, listing folder contents, "
        "reading files, and manipulating system resources directly through the command line interface.")

    # CONTENT_MASTER
    GPT_002 = "CONTENT_MASTER", (
        "Select this model exclusively for creating, generating, and saving any type of content, including text, code, "
        "images, and others. This model should always be used when the task involves generating or saving content.")

    # TEXT_ANALYZER
    GPT_003 = "TEXT_ANALYZER", (
        "Select this model for extracting and processing information from within individual documents and files, "
        "focusing on text analysis and content within a single file.")

    # DATA_ANALYSIS
    GPT_004 = "DATA_ANALYSIS", (
        "Select this model for analyzing datasets, performing statistical analysis, and generating reports. Media "
        "Management and Playback: Select this model for organizing, categorizing, and playing multimedia content.")

    # CHAT_MASTER
    GPT_005 = "CHAT_MASTER", (
        "Select this model for providing conversational responses or engaging in general chat.")

    # MEDIA_MANAGEMENT_AND_PLAYBACK
    GPT_006 = "MEDIA_MANAGEMENT_AND_PLAYBACK", (
        "Media Management and Playback: Select this model for organizing, categorizing, and playing "
        "multimedia content.")

    # IMAGE_PROCESSOR
    GPT_007 = "IMAGE_PROCESSOR", (
        "Select this model to execute tasks exclusively related to images, such as image captioning, face "
        "recognition, and comprehensive visual analysis.")

    # ASSISTIVE_TECH_HELPER
    GPT_008 = "ASSISTIVE_TECH_HELPER", (
        "Select this model for any tasks initiated or involving assistive technologies such as STT "
        "(Speech-To-Text) and TTS (Text-To-Speech).")

    # SUMMARIZE_AND_QUERY
    GPT_009 = "SUMMARIZE_AND_QUERY", (
        "Select this model upon receiving an explicit user request for 'summarization of files and folders'.")

    # WEB_FETCH
    GPT_010 = "WEB_FETCH", (
        "Select this model for retrieving information from the web.")

    # FINAL_ANSWER
    GPT_011 = "FINAL_ANSWER", (
        "Select this model to provide a clear and definitive answer to the human.")

    @classmethod
    def enlist(cls, separator: str = os.linesep) -> str:
        """Return a list of selectable models."""
        return separator.join(f"{m}: {v[1]}" for m, v in zip(cls.names(), cls.values()))

    def __str__(self):
        return f"{self.name}::{self.value[1]}"

    def __repr__(self):
        return str(self)

    # fmt: on


if __name__ == '__main__':
    print(RoutingModel.enlist())
