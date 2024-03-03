import logging as log
from typing import Tuple, Optional, Any

from langchain_core.prompts import PromptTemplate

from askai.core.askai_messages import AskAiMessages
from askai.core.askai_prompt import AskAiPrompt
from askai.core.component.cache_service import CacheService
from askai.core.model.query_response import QueryResponse
from askai.core.processor.ai_processor import AIProcessor
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared


class GenericProcessor(AIProcessor):
    """Process a generic question process."""

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
        return (
            'Prompts for general content retrieval from the database. '
            'This type is selected when no other prompts are suitable for the query.'
        )

    def template(self) -> str:
        return AskAiPrompt.INSTANCE.read_template('generic-prompt')

    def process(self, query_response: QueryResponse) -> Tuple[bool, Optional[str]]:
        status = False
        output = None
        template = PromptTemplate(input_variables=['history', 'question', 'user'], template=self.template())
        context = str(shared.context.get_many("GENERIC"))
        final_prompt: str = template.format(
            history=context, question=query_response.question, user=AskAiPrompt.INSTANCE.user)
        llm: Any = lc_llm.create_langchain_model(temperature=1, top_p=1)
        log.info("%s::[QUESTION] '%s'", self.name, final_prompt)
        try:
            output = llm(final_prompt).strip().replace('RESPONSE: ', '')
            CacheService.save_reply(query_response.question, query_response.question)
            CacheService.save_query_history()
            shared.context.push("GENERIC", query_response.question)
            shared.context.push("GENERIC", output, 'assistant')
            status = True
        except Exception as err:
            status = False
            output = AskAiMessages.INSTANCE.llm_error(str(err))
        finally:
            return status, output

    def next_in_chain(self) -> Optional['AIProcessor']:
        return None
