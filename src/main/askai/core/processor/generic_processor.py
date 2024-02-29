import logging as log
from typing import Tuple, Optional

from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate

from askai.core.askai_prompt import AskAiPrompt
from askai.core.component.cache_service import CacheService
from askai.core.model.query_response import QueryResponse
from askai.core.processor.ai_processor import AIProcessor


class GenericProcessor(AIProcessor):
    """Process a generic question process."""

    def __str__(self):
        return f"\"{self.query_type()}\": {self.query_desc()}"

    def supports(self, q_type: str) -> bool:
        return q_type == self.query_type()

    def processor_id(self) -> str:
        return str(abs(hash(self.__class__.__name__)))

    def query_type(self) -> str:
        return f"Type-{self.processor_id()}"

    def query_desc(self) -> str:
        return 'Prompts about general content that can be retrieved from your database.'

    def template(self) -> str:
        return AskAiPrompt.INSTANCE.read_template('generic-prompt')

    def process(self, query_response: QueryResponse) -> Tuple[bool, Optional[str]]:
        llm = OpenAI(temperature=0.6, top_p=0.8)
        template = PromptTemplate(input_variables=['question'], template=self.template())
        final_prompt: str = template.format(question=query_response.question)
        log.info("GenericProcessor QUESTION: '%s'", final_prompt)
        try:
            output = llm(final_prompt).strip().replace('RESPONSE: ', '')
            CacheService.save_reply(query_response.question, query_response.question)
            CacheService.save_query_history()
            return True, output
        except Exception as err:
            return False, f"LLM returned an error: {str(err)}"

    def next_in_chain(self) -> Optional['AIProcessor']:
        return None

