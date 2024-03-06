import logging as log
from typing import Tuple, Optional, List

from hspylib.core.tools.text_tools import ensure_startswith
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
        context: List[dict] = shared.context.get_many("ANALYSIS", "OUTPUT", "SETUP", "QUESTION")
        log.info("%s::[QUESTION] '%s'", self.name, context)
        try:
            if (response := shared.engine.ask(context, temperature=0.0, top_p=0.0)) and response.is_success:
                if output := response.message:
                    shared.context.set("ANALYSIS", output, 'assistant')
                    output = ensure_startswith(output, AskAiMessages.INSTANCE.analysis_output())
                CacheService.save_query_history()
                status = True
            else:
                output = AskAiMessages.INSTANCE.llm_error(response.message)
        # except Exception as err:
        #     output = AskAiMessages.INSTANCE.llm_error(str(err))
        finally:
            return status, output

    def next_in_chain(self) -> Optional['AIProcessor']:
        return None
