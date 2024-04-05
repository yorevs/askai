import logging as log
import os
import re
from functools import lru_cache
from typing import TypeAlias, Tuple, Optional

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
from askai.core.model.processor_response import ProcessorResponse
from askai.core.proxy.features import features
from askai.core.proxy.tools.general import assert_accuracy
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.exception.exceptions import InaccurateResponse, MaxInteractionReached

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

    @retry(exceptions=InaccurateResponse, tries=3, delay=0, backoff=0)
    def process(self, question: str) -> Tuple[bool, ProcessorResponse]:
        status = False
        template = PromptTemplate(input_variables=['features', 'objective'], template=self.template())
        final_prompt = template.format(features=features.enlist(), objective=question)
        ctx: str = shared.context.flat("OUTPUT", "ANALYSIS", "INTERNET", "GENERAL")
        log.info("Router::[QUESTION] '%s'  context: '%s'", question, ctx)
        chat_prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
        chain = create_stuff_documents_chain(lc_llm.create_chat_model(), chat_prompt)
        context = [Document(ctx)]

        if response := chain.invoke({"query": final_prompt, "context": context}):
            log.info("Router::[RESPONSE] Received from AI: \n%s.", str(response))
            output = self._route(question, re.sub(r'\d+[.:)-]\s+', '', response))
            status = True
        else:
            output = response

        return status, ProcessorResponse(response=output)

    def _route(self, question: str, action_plan: str) -> Optional[str]:
        """Route the actions to the proper function invocations."""
        tasks: list[str] = list(map(str.strip, action_plan.split(os.linesep)))
        max_actions: int = 20
        result: str = ''
        for idx, action in enumerate(tasks):
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=f"`{action}`", verbosity='debug')
            if idx > max_actions:
                AskAiEvents.ASKAI_BUS.events.reply_error.emit(message=msg.too_many_actions())
                raise MaxInteractionReached(f"Maximum number of action was reached")
            if not (result := features.invoke(action, result)):
                break

        return assert_accuracy(question, result)


assert (router := Router().INSTANCE) is not None
