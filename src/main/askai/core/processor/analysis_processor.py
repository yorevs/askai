from typing import Tuple, Optional

from askai.core.askai_prompt import AskAiPrompt
from askai.core.model.query_response import QueryResponse
from askai.core.processor.ai_processor import AIProcessor


class AnalysisProcessor(AIProcessor):
    """Process an analysis question process."""

    def __str__(self):
        return f"\"{self.query_type()}\": {self.query_desc()}"

    @property
    def name(self) -> str:
        return type(self).__name__

    def supports(self, q_type: str) -> bool:
        return q_type == self.query_type()

    def processor_id(self) -> str:
        return str(abs(hash(self.__class__.__name__)))

    def query_type(self) -> str:
        return self.name

    def query_desc(self) -> str:
        return "Prompts where the user asks questions about command outputs, previously provided by him."

    def template(self) -> str:
        return AskAiPrompt.INSTANCE.read_template('analysis-prompt')

    def process(self, query_response: QueryResponse) -> Tuple[bool, Optional[str]]:
        return True, query_response.response

    def next_in_chain(self) -> Optional['AIProcessor']:
        return None
