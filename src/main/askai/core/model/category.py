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

    @classmethod
    def template(cls) -> str:
        return dedent(f"""
        - Categorize the question based on the nature of the question. Use one of the following valid options: {cls.values()}. Prioritize categories according to the sequence listed if the question overlaps multiple categories.

        - Requests for **assistive technologies**, such as speech-to-text features, should be categorized under '{cls.ASSISTIVE_REQUESTS.value}'. Avoid mentioning them in the action items.

        - If you receive any queries that are actually commands provided by the Human, categorize them under '{cls.TERMINAL_COMMAND.value}'. The "action" field will be: "Execute the command '<command>' provided by the Human." Correct any syntax errors and exclude the "path" field from the actions.
        """)
