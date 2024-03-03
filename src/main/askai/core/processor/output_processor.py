import logging as log
from typing import Tuple, Optional

from langchain_core.prompts import PromptTemplate

from askai.core.askai_messages import AskAiMessages
from askai.core.askai_prompt import AskAiPrompt
from askai.core.model.query_response import QueryResponse
from askai.core.processor.ai_processor import AIProcessor
from askai.core.support.langchain_support import lc_llm


class OutputProcessor(AIProcessor):
    """Process a command output process."""

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
        return "Prompts where I will provide you a terminal command output."

    def template(self) -> str:
        return AskAiPrompt.INSTANCE.read_template('output-prompt')

    def process(self, query_response: QueryResponse) -> Tuple[bool, Optional[str]]:
        status = False
        output = None
        llm = lc_llm.create_langchain_model(temperature=0.0, top_p=0.0)
        template = PromptTemplate(
            input_variables=['command_line', 'shell', 'command_output'],
            template=self.template()
        )
        final_prompt: str = template.format(
            command_line='; '.join([c.cmd_line for c in query_response.commands]),
            shell=AskAiPrompt.INSTANCE.shell,
            command_output='\n'.join([c.cmd_out for c in query_response.commands])
        )
        log.info("%s::[QUESTION] '%s'", self.name, final_prompt)
        try:
            output = llm(final_prompt).lstrip()
            status = True
        except Exception as err:
            status = False
            output = AskAiMessages.INSTANCE.llm_error(str(err))
        finally:
            return status, output

    def next_in_chain(self) -> Optional['AIProcessor']:
        return None
