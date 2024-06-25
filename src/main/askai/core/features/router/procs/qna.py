from typing import Optional

from hspylib.core.metaclass.singleton import Singleton

from askai.core.askai_messages import msg
from askai.core.component.summarizer import summarizer
from askai.core.support.utilities import display_text


class QnA(metaclass=Singleton):
    """Processor to provide a questions and answers session about a summarized context."""

    INSTANCE: "QnA"

    def process(self, question: str, **_) -> Optional[str]:
        """Process the user question against a summarized context to retrieve answers.
        :param question: The user question to process.
        """
        if not (output := summarizer.query_one(question)):
            display_text(f"# {msg.leave_qna()} %EOL%")
            output = msg.welcome_back()
        return output


assert (qna := QnA().INSTANCE) is not None
