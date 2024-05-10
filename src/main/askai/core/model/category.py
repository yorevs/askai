from textwrap import dedent

from hspylib.core.enums.enumeration import Enumeration


class Category(Enumeration):
    """TODO"""

    # fmt: off

    CREATIONAL                          = 'Creational'

    DATA_ANALYSIS                       = 'Data Analysis'

    MEDIA_MANAGEMENT_AND_PLAYBACK       = 'Media Management and Playback'

    CONVERSATIONAL                      = 'Conversational'

    IMAGE_CAPTION                       = 'Image Caption'

    INFORMATION_RETRIEVAL               = 'Information Retrieval'

    ASSISTIVE_REQUESTS                  = 'Assistive Requests'

    FILE_MANAGEMENT                     = 'File Management'

    TERMINAL_COMMAND                    = 'Terminal Command'

    SUMMARIZATION                       = 'Summarization'

    FINAL_ANSWER                        = 'Final Answer'

    # fmt: on
