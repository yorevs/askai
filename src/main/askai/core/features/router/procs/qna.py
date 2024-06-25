from string import Template
from textwrap import dedent
from typing import Optional

from hspylib.core.metaclass.singleton import Singleton


class QnA(metaclass=Singleton):
    """Processor to provide a quesations and answers session about a summarized context."""

    INSTANCE: "QnA"

    # This is required because the AI sometimes forgets to wrap the response in a Json object.
    HUMAN_PROMPT: str = Template(dedent(
        """
        Human Question: "${input}"
        """).strip())

    def process(self, question: str, **kwargs) -> Optional[str]:
        """Process the user question against a summarized context to retrieve answers.
        :param question: The user question to process.
        """
        pass
