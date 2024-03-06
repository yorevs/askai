import logging as log
from typing import Tuple, Optional, List

from langchain_core.prompts import PromptTemplate

from askai.core.askai_messages import AskAiMessages
from askai.core.askai_prompt import AskAiPrompt
from askai.core.component.cache_service import CacheService
from askai.core.model.query_response import QueryResponse
from askai.core.processor.ai_processor import AIProcessor
from askai.core.support.shared_instances import shared


class GenericProcessor(AIProcessor):
    """Process a generic question process."""

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
        return (
            "This prompt type is ideal for engaging in casual conversations between you and me, covering a wide range "
            "of everyday topics and general discussions."
        )

    def template(self) -> str:
        return AskAiPrompt.INSTANCE.read_template('generic-prompt')

    def process(self, query_response: QueryResponse) -> Tuple[bool, Optional[str]]:
        status = False
        output = None
        template = PromptTemplate(
            input_variables=['user'], template=self.template())
        final_prompt: str = AskAiMessages.INSTANCE.translate(
            template.format(user=AskAiPrompt.INSTANCE.user))
        shared.context.set("SETUP", final_prompt, 'system')
        shared.context.set("QUESTION", query_response.question)
        context: List[dict] = shared.context.get_many("GENERAL", "SETUP", "QUESTION")
        log.info("%s::[QUESTION] '%s'", self.name, context)
        try:
            if (response := shared.engine.ask(context, temperature=1, top_p=1)) and response.is_success:
                output = response.message
                CacheService.save_reply(query_response.question, query_response.question)
                CacheService.save_query_history()
                shared.context.push("GENERAL", output, 'assistant')
                status = True
            else:
                output = AskAiMessages.INSTANCE.llm_error(response.message)
        # except Exception as err:
        #     output = AskAiMessages.INSTANCE.llm_error(str(err))
        finally:
            return status, output

    def next_in_chain(self) -> Optional['AIProcessor']:
        return None
