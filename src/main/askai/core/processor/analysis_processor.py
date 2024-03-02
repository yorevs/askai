import logging as log
from typing import Tuple, Optional

from langchain_core.prompts import PromptTemplate

from askai.core.askai_messages import AskAiMessages
from askai.core.askai_prompt import AskAiPrompt
from askai.core.component.cache_service import CacheService
from askai.core.model.query_response import QueryResponse
from askai.core.processor.ai_processor import AIProcessor
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared


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
        llm = lc_llm.create_langchain_model(temperature=1, top_p=1)
        template = PromptTemplate(input_variables=['context', 'question'], template=self.template())
        context = str(shared.context.get_many("COMMAND", "OUTPUT", "LAST_DIR", "ANALYSIS"))
        final_prompt: str = template.format(context=context, question=query_response.question)
        log.info("%s::[QUESTION] '%s'", self.name, final_prompt)
        try:
            output = llm(final_prompt).strip().replace('RESPONSE: ', '')
            CacheService.save_query_history()
            shared.context.push("ANALYSIS", query_response.question)
            shared.context.push("ANALYSIS", output, 'assistant')
            return True, output
        except Exception as err:
            log.error(err)
            return False, AskAiMessages.INSTANCE.llm_error(str(err))

    def next_in_chain(self) -> Optional['AIProcessor']:
        return None
