from functools import cached_property
from typing import Optional, Tuple

from askai.core.askai_prompt import AskAiPrompt
from askai.core.model.query_response import QueryResponse
from askai.core.processor.ai_processor import AIProcessor


class CommandProcessor(AIProcessor):
    """Process a command based question process."""

    def __init__(self, query_response: QueryResponse = None):
        self._response = query_response

    def __str__(self):
        return f"{self.query_name()}: {self.query_desc()}"

    def supports(self, q_type: str) -> bool:
        return q_type == self.query_name

    def processor_id(self) -> str:
        return str(abs(hash(self.__class__.__name__)))

    def query_name(self) -> str:
        return f"Type-{self.processor_id()}"

    def query_desc(self) -> str:
        return (
            "Prompts that will require you to execute commands at the user's terminal "
            "(Example: list files and folders)."
    )

    def prompt(self) -> str:
        return AskAiPrompt.INSTANCE.read_prompt('command-prompt')

    def process(self, query_response: QueryResponse) -> Tuple[bool, str]:
        return True, self._response.response

    def prev_in_chain(self) -> Optional[AIProcessor]:
        return None

    def next_in_chain(self) -> Optional[AIProcessor]:
        return None
