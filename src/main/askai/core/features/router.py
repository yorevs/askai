import logging as log
import os
import re
from functools import lru_cache
from typing import TypeAlias, Optional

from hspylib.core.metaclass.singleton import Singleton
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.runnables.utils import Input, Output
from retry import retry

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperature import Temperature
from askai.core.features.actions import features
from askai.core.model.rag_response import RagResponse
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
            log.info("Assert::[QUESTION] '%s'  context: '%s'", question, ai_response)

            llm = lc_llm.create_chat_model(Temperature.CREATIVE_WRITING.temp)
            chat_prompt = ChatPromptTemplate.from_messages([("system", "{context}\n\n{query}")])
            chain = create_stuff_documents_chain(llm, chat_prompt)
            context = [Document(ai_response)]
            output = chain.invoke({"query": final_prompt, "context": context})

            if output and (mat := RagResponse.matches(output)):
                status, reason = mat.group(1), mat.group(2)
                log.info("Accuracy  status: '%s'  reason: '%s'", status, reason)
                AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.assert_acc(output), verbosity='debug')
                if RagResponse.of_value(status.strip()).is_bad:
                    raise InaccurateResponse(RagResponse.strip_code(output))
                return ai_response

        raise InaccurateResponse(f"The AI Assistant fit not respond properly!")

    def process(self, query: str) -> Optional[str]:
        """Process the user query and retrieve the final response."""
        @retry(exceptions=InaccurateResponse, tries=2, delay=0, backoff=0)
        def _process_wrapper(question: str) -> Optional[str]:
            """Wrapper to allow RAG retries."""
            template = PromptTemplate(input_variables=[
                'features', 'objective', 'os_type'
            ], template=self.template())
            ctx: str = shared.context.flat("CONTEXT")
            final_prompt = template.format(
                features=features.enlist(), objective=question, os_type=prompt.os_type)
            log.info("Router::[QUESTION] '%s'  context: '%s'", question, ctx)

            chat_prompt = ChatPromptTemplate.from_messages([("system", "{context}\n\n{query}")])
            chain = create_stuff_documents_chain(lc_llm.create_chat_model(Temperature.DATA_ANALYSIS.temp), chat_prompt)
            context = [Document(ctx)]

            if response := chain.invoke({"query": final_prompt, "context": context}):
                log.info("Router::[RESPONSE] Received from AI: \n%s.", str(response))
                output = self._route(question, re.sub(r'\d+[.:)-]\s+', '', response))
            else:
                output = response
            return output

        return _process_wrapper(query)

    def _route(self, question: str, action_plan: str) -> Optional[str]:
        """Route the actions to the proper function invocations."""
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
