from functools import cached_property
from typing import Optional, Tuple

from askai.core.askai_prompt import AskAiPrompt
from askai.core.model.query_response import QueryResponse
from askai.core.processor.ai_processor import AIProcessor


class GenericProcessor(AIProcessor):
    """Process a generic question process."""

    def __init__(self, query_response: QueryResponse = None):
        self._response = query_response

    def __str__(self):
        return f"{self.query_name()}: {self.query_desc()}"

    def supports(self, q_type: str) -> bool:
        return q_type == self.query_name

    @cached_property
    def processor_id(self):
        return hash(self.__class__.__name__)

    def query_name(self) -> str:
        return f"Type-{self.processor_id}"

    def query_desc(self) -> str:
        return "Prompts about content that can be retrieved from your database."

    def prompt(self) -> str:
        return AskAiPrompt.INSTANCE.read_prompt('generic-prompt')

    def process(self) -> Tuple[bool, str]:
        return True, self._response.response

    def prev_in_chain(self) -> Optional[AIProcessor]:
        return None

    def next_in_chain(self) -> Optional[AIProcessor]:
        return None
