import logging as log
from typing import Tuple, Optional

from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI

from askai.core.askai_prompt import AskAiPrompt
from askai.core.model.query_response import QueryResponse
from askai.core.processor.ai_processor import AIProcessor


class OutputProcessor(AIProcessor):
    """Process a command output process."""

    def __init__(self):
        self._llm: OpenAI = OpenAI(temperature=0.0, top_p=0.0)

    def __str__(self):
        return f"\"{self.query_type()}\": {self.query_desc()}"

    def supports(self, q_type: str) -> bool:
        return q_type == self.query_type()

    def processor_id(self) -> str:
        return str(abs(hash(self.__class__.__name__)))

    def query_type(self) -> str:
        return f"Type-{self.processor_id()}"

    def query_desc(self) -> str:
        return "Prompts where I will provide you a terminal command output."

    def template(self) -> str:
        return AskAiPrompt.INSTANCE.read_template('generic-prompt')

    def process(self, query_response: QueryResponse) -> Tuple[bool, Optional[str]]:
        status = False
        output = None
        command_output = query_response.response
        template = PromptTemplate(
            input_variables=['command_line', 'command_output'],
            template=self.template()
        )
        final_prompt: str = template.format(
            command_line='; '.join([c.cmd_line for c in query_response.commands]),
            command_output='\n'.join([c.cmd_out for c in query_response.commands])
        )
        log.info("CommandProcessor QUESTION: '%s'", final_prompt)
        return status, output

    def next_in_chain(self) -> Optional['AIProcessor']:
        return None
