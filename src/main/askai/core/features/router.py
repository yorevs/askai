import logging as log
import os
import re
from functools import lru_cache
from typing import TypeAlias, Optional

from hspylib.core.metaclass.singleton import Singleton
from langchain.globals import set_llm_cache
from langchain_community.cache import InMemoryCache
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.runnables.utils import Input, Output
from retry import retry

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperature import Temperature
from askai.core.model.rag_response import RagResponse
from askai.core.features.actions import features
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.exception.exceptions import InaccurateResponse, MaxInteractionsReached

RunnableTool: TypeAlias = Runnable[list[Input], list[Output]]


class Router(metaclass=Singleton):
    """Class to provide a divide and conquer set of actions to fulfill an objective. This is responsible for the
    orchestration and execution of the actions."""

    INSTANCE: 'Router' = None

    def __init__(self):
        self._approved = False

    @lru_cache
    def template(self) -> str:
        return prompt.read_prompt("router-prompt.txt")

    @staticmethod
    def _assert_accuracy(question: str, ai_response: str) -> Optional[str]:
        """Function responsible for asserting that the question was properly answered."""
        if ai_response:
            template = PromptTemplate(input_variables=[
                'question', 'response'
            ], template=prompt.read_prompt('rag-prompt'))
            final_prompt = template.format(
                question=question, response=ai_response or '')
            llm = lc_llm.create_chat_model(Temperature.DATA_ANALYSIS.temp)
            if (output := llm.predict(final_prompt)) and (mat := RagResponse.matches(output)):
                status, reason = mat.group(1), mat.group(2)
                log.info("Accuracy  status: '%s'  reason: '%s'", status, reason)
                AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.assert_acc(output), verbosity='debug')
                if RagResponse.of_value(status.strip()).is_bad:
                    raise InaccurateResponse(f"The RAG response was not 'Green' => '{output}' ")
            return ai_response

        raise InaccurateResponse(f"The RAG response was not 'Green'")

    def process(self, query: str) -> Optional[str]:
        """Process the user query and retrieve the final response."""
        @retry(exceptions=InaccurateResponse, tries=2, delay=0, backoff=0)
        def _process_wrapper(question: str) -> Optional[str]:
            """Wrapper to allow RAG retries."""
            template = PromptTemplate(input_variables=[
                'features', 'context', 'objective'
            ], template=self.template())
            context: str = shared.context.flat("OUTPUT", "ANALYSIS", "INTERNET", "GENERAL")
            final_prompt = template.format(
                features=features.enlist(), context=context or 'Nothing yet', objective=question)
            log.info("Router::[QUESTION] '%s'  context: '%s'", question, context)
            llm = lc_llm.create_chat_model(Temperature.DATA_ANALYSIS.temp)

            if response := llm.predict(final_prompt):
                log.info("Router::[RESPONSE] Received from AI: \n%s.", str(response))
                output = self._route(question, re.sub(r'\d+[.:)-]\s+', '', response))
            else:
                output = response
            return output

        return _process_wrapper(query)

    def _route(self, question: str, action_plan: str) -> Optional[str]:
        """Route the actions to the proper function invocations."""
        set_llm_cache(InMemoryCache())
        tasks: list[str] = list(map(str.strip, action_plan.split(os.linesep)))
        max_actions: int = 20  # TODO Move to configs
        result: str = ''
        for idx, action in enumerate(tasks):
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=f"`{action}`", verbosity='debug')
            if idx > max_actions:
                AskAiEvents.ASKAI_BUS.events.reply_error.emit(message=msg.too_many_actions())
                raise MaxInteractionsReached(f"Maximum number of action was reached")
            if not (result := features.invoke(question, action, result)):
                log.warning("Last result brought an empty response for '%s'", action)
                break

        return self._assert_accuracy(question, result)


assert (router := Router().INSTANCE) is not None
