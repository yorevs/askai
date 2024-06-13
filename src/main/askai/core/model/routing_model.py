import os

from hspylib.core.enums.enumeration import Enumeration


class RoutingModel(Enumeration):
    """TODO"""

    # fmt: on

    ASK_000 = (
        "NEUTRAL", "Select this model when no other model fits the user request."
    )

    # TERMINAL_COMMAND
    ASK_001 = "TERMINAL_COMMAND", (
        "Select this model for executing shell commands, managing terminal operations, listing folder contents, "
        "reading files, and manipulating system resources directly through the command line interface.")

    # CONTENT_MASTER
    ASK_002 = "CONTENT_MASTER", (
        "Select this model exclusively for creating, generating, and saving any type of content, including text, code, "
        "images, and others. This model should always be used when the task involves generating or saving content.")

    # TEXT_ANALYZER
    ASK_003 = "TEXT_ANALYZER", (
        "Select this model for extracting and processing information from within individual documents and files, "
        "focusing on text analysis and content within a single file.")

    # DATA_ANALYSIS
    ASK_004 = "DATA_ANALYSIS", (
        "Select this model for analyzing datasets, performing statistical analysis, and generating reports. Media "
        "Management and Playback: Select this model for organizing, categorizing, and playing multimedia content.")

    # CHAT_MASTER
    ASK_005 = "CHAT_MASTER", (
        "Select this model for providing conversational responses or engaging in general chat.")

    # MEDIA_MANAGEMENT_AND_PLAYBACK
    ASK_006 = "MEDIA_MANAGEMENT_AND_PLAYBACK", (
        "Select this model for organizing, categorizing, and playing multimedia content.")

    # IMAGE_PROCESSOR
    ASK_007 = "IMAGE_PROCESSOR", (
        "Select this model to execute tasks exclusively related to images, such as image captioning, face "
        "recognition, and comprehensive visual analysis.")

    # ASSISTIVE_TECH_HELPER
    ASK_008 = "ASSISTIVE_TECH_HELPER", (
        "Select this model for any tasks initiated or involving assistive technologies such as STT "
        "(Speech-To-Text) and TTS (Text-To-Speech).")

    # SUMMARIZE_AND_QUERY
    ASK_009 = "SUMMARIZE_AND_QUERY", (
        "Select this model upon receiving an explicit user request for 'summarization of files and folders'.")

    # WEB_FETCH
    ASK_010 = "WEB_FETCH", (
        "Select this model for retrieving information from the web.")

    # FINAL_ANSWER
    ASK_011 = "FINAL_ANSWER", (
        "Select this model to provide a clear and definitive answer to the human.")

    @classmethod
    def enlist(cls, separator: str = os.linesep) -> str:
        """Return a list of selectable models."""
        return separator.join(f"{m}: {v[1]}" for m, v in zip(cls.names(), cls.values()))

    def __str__(self):
        return f"{self.name}::{self.category}"

    def __repr__(self):
        return str(self)

    @property
    def model(self) -> str:
        return self.name

    @property
    def category(self) -> str:
        return self.value[0]

    @property
    def description(self) -> str:
        return self.value[1]

    # fmt: on


if __name__ == '__main__':
    print(RoutingModel.enlist())
