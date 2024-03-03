import logging as log
from typing import Tuple, Optional, List

from askai.core.askai_messages import AskAiMessages
from askai.core.askai_prompt import AskAiPrompt
from askai.core.component.cache_service import CacheService
from askai.core.model.query_response import QueryResponse
from askai.core.processor.ai_processor import AIProcessor
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
        status = False
        output = None
        shared.context.set("SETUP", self.template(), 'system')
        shared.context.set("QUESTION", query_response.question)
        context: List[dict] = shared.context.get_many("SETUP", "OUTPUT", "ANALYSIS", "QUESTION")
        log.info("%s::[QUESTION] '%s'", self.name, context)
        try:
            if (response := shared.engine.ask(context, temperature=0.0, top_p=0.0)) and response.is_success():
                output = response.reply_text()
                CacheService.save_query_history()
                shared.context.set("ANALYSIS", output)
                status = True
            else:
                output = AskAiMessages.INSTANCE.llm_error(response.reply_text())
        except Exception as err:
            status = False
            output = AskAiMessages.INSTANCE.llm_error(str(err))
        finally:
            return status, output

    def next_in_chain(self) -> Optional['AIProcessor']:
        return None
