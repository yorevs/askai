import logging as log
from typing import Tuple, Optional, List

from langchain_core.prompts import PromptTemplate

from askai.core.askai_messages import AskAiMessages
from askai.core.askai_prompt import AskAiPrompt
from askai.core.model.query_response import QueryResponse
from askai.core.processor.ai_processor import AIProcessor
from askai.core.support.shared_instances import shared


class OutputProcessor(AIProcessor):
    """Process a command output process."""

    def __str__(self):
        return f"'{self.query_type()}': {self.query_desc()}"

    @property
    def name(self) -> str:
        return type(self).__name__

    def supports(self, q_type: str) -> bool:
        return q_type in [self.query_type()]

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
        shell = AskAiPrompt.INSTANCE.shell
        commands = '; '.join([c.cmd_line for c in query_response.commands])
        output = '\n'.join([c.cmd_out for c in query_response.commands])
        template = PromptTemplate(
            input_variables=['command_line', 'shell'],
            template=self.template()
        )
        final_prompt: str = AskAiMessages.INSTANCE.translate(template.format(
            command_line=commands,
            shell=shell
        ))
        shared.context.set("SETUP", final_prompt, 'system')
        context: List[dict] = shared.context.get_many("CONTEXT", "SETUP")
        log.info("Output::[COMMAND] '%s'  context=%s", commands, context)
        try:
            if (response := shared.engine.ask(context, temperature=0.0, top_p=0.0)) and response.is_success:
                log.debug('Output::[RESPONSE] Received from AI: %s.', response)
                if output := response.message:
                    shared.context.push("CONTEXT", output, 'assistant')
                status = True
            else:
                log.error(f"Output processing failed. CONTEXT=%s  RESPONSE=%s", context, response)
                output = AskAiMessages.INSTANCE.llm_error(response.message)
        finally:
            return status, output

    def next_in_chain(self) -> Optional['AIProcessor']:
        return None
