import logging as log
from typing import Tuple, Optional

from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI

from askai.core.component.cache_service import CacheService
from askai.core.model.query_response import QueryResponse
from askai.core.processor.ai_processor import AIProcessor
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
        return shared.prompt.read_template('generic-prompt')

    def process(self, query_response: QueryResponse) -> Tuple[bool, Optional[str]]:
        llm = OpenAI(temperature=0.6, top_p=0.8)
        template = PromptTemplate(input_variables=['question', 'user'], template=self.template())
        final_prompt: str = template.format(question=query_response.question, user=shared.prompt.user)
        log.info("%s::[QUESTION] '%s'", self.name, final_prompt)
        try:
            output = llm(final_prompt).strip().replace('RESPONSE: ', '')
            CacheService.save_reply(query_response.question, query_response.question)
            CacheService.save_query_history()
            return True, output
        except Exception as err:
            log.error(err)
            return False, shared.msg.llm_error(str(err))

    def next_in_chain(self) -> Optional['AIProcessor']:
        return None

