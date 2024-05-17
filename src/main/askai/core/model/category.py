from hspylib.core.enums.enumeration import Enumeration


class Category(Enumeration):
    """TODO"""

    # fmt: off

    TERMINAL_COMMAND                = 'Terminal Command', \
                                          'Select this model for executing shell commands, managing terminal operations, listing folder contents, reading files, and manipulating system resources directly through the command line interface.'
    CONTENT_MASTER                  = 'Content Master', \
                                          'Select this model exclusively for creating, generating, and saving any type of content, including text, code, images, and others. This model should always be used when the task involves generating or saving content.'
    TEXT_ANALYZER                   = 'Text Analyzer', \
                                          'Select this model for extracting and processing information from within documents and files, focusing on text analysis and content without direct file system operations.'
    CHAT_MASTER                     = 'Chat Master', \
                                          'Select this model for analyzing datasets, performing statistical analysis, and generating reports.'
    DATA_ANALYSIS                   = 'Data Analysis', \
                                          'Select this model for organizing, categorizing, and playing multimedia content.'
    WEB_FETCH                       = 'Web Fetch', \
                                          'Select this model for providing conversational responses or engaging in general chat.'
    IMAGE_PROCESSOR                 = 'Image Processor', \
                                          'Select this model for processing images, and performing recognition, and manipulation tasks.'
    MEDIA_MANAGEMENT_AND_PLAYBACK   = 'Media Management and Playback', \
                                          'Select this model for any tasks initiated or involving assistive technologies such as STT (Speech-To-Text) and TTS (Text-To-Speech).'
    ASSISTIVE_TECH_HELPER           = 'Assistive Tech. Helper', \
                                          'Select this model when the user explicitly requests summarizing files and folders.'
    SUMMARIZE_AND_QUERY             = 'Summarize and Query', \
                                          'Select this model for retrieving information from the web.'
    FINAL_ANSWER                    = 'Final Answer', \
                                          'Select this model to provide a clear and definitive answer to the human.'

    # fmt: on
