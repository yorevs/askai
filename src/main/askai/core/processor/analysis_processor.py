import logging as log
from typing import Tuple, Optional, List

from langchain_core.prompts import PromptTemplate

from askai.core.askai_messages import AskAiMessages
from askai.core.askai_prompt import AskAiPrompt
from askai.core.component.cache_service import CacheService
from askai.core.model.query_response import QueryResponse
from askai.core.processor.ai_processor import AIProcessor
from askai.core.support.shared_instances import shared


class AnalysisProcessor(AIProcessor):
    """Process an analysis question process."""

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
            "Prompts that leverage prior command outputs in the chat history. These prompts may involve "
            "file management, data, file or folder inquiries, yes/no questions, and more, all answerable by "
            "referencing earlier command outputs in conversation history. Please prioritize this "
            "query type to be selected when you see command outputs in chat history."
        )

    def template(self) -> str:
        return AskAiPrompt.INSTANCE.read_template('analysis-prompt')

    def process(self, query_response: QueryResponse) -> Tuple[bool, Optional[str]]:
        status = False
        output = None
        template = PromptTemplate(
            input_variables=[], template=self.template())
        final_prompt: str = AskAiMessages.INSTANCE.translate(template.format())
        shared.context.set("SETUP", final_prompt, 'system')
        shared.context.set("QUESTION", query_response.question)
        context: List[dict] = shared.context.get_many("CONTEXT", "SETUP", "QUESTION")
        log.info("Analysis::[QUESTION] '%s'  context=%s", query_response.question, context)
        try:
            if (response := shared.engine.ask(context, temperature=0.0, top_p=0.0)) and response.is_success:
                log.debug('Analysis::[RESPONSE] Received from AI: %s.', response)
                if output := response.message:
                    shared.context.push("CONTEXT", query_response.question)
                    shared.context.push("CONTEXT", output, 'assistant')
                CacheService.save_query_history()
                status = True
            else:
                log.error(f"Analysis processing failed. CONTEXT=%s  RESPONSE=%s", context, response)
                output = AskAiMessages.INSTANCE.llm_error(response.message)
        finally:
            return status, output

    def next_in_chain(self) -> Optional['AIProcessor']:
        return None
