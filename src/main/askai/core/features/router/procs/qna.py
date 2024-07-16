from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.component.summarizer import summarizer
from askai.core.model.summary_result import SummaryResult
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_state
from typing import Optional


class QnA(metaclass=Singleton):
    """Processor to provide a questions and answers session about a summarized context."""

    INSTANCE: "QnA"

    def process(self, question: str, **_) -> Optional[str]:
        """Process the user question against a summarized context to retrieve answers.
        :param question: The user question to process.
        """
        if question.casefold() == "exit" or not (response := summarizer.query(question)):
            events.mode_changed.emit(mode="DEFAULT")
            output = msg.leave_qna()
        else:
            check_state(isinstance(response[0], SummaryResult))
            output = response[0].answer

        return output


assert (qna := QnA().INSTANCE) is not None
