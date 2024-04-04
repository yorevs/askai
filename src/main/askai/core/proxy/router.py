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

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.geo_location import geo_location
from askai.core.model.processor_response import ProcessorResponse
from askai.core.proxy.features import features
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared

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

    def process(self, question: str) -> Tuple[bool, ProcessorResponse]:
        status = False
        template = PromptTemplate(input_variables=[
            'features', 'os_type', 'shell', 'idiom', 'location', 'datetime', 'question'
        ], template=self.template())
        final_prompt = template.format(
            os_type=prompt.os_type, shell=prompt.shell, idiom=shared.idiom,
            location=geo_location.location, datetime=geo_location.datetime,
            question=question, features=features.enlist()
        )
        ctx: str = shared.context.flat("GENERAL", "INTERNET", "OUTPUT", "ANALYSIS")
        log.info("Router::[QUESTION] '%s'  context: '%s'", question, ctx)
        chat_prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
        chain = create_stuff_documents_chain(lc_llm.create_chat_model(), chat_prompt)
        context = [Document(ctx)]

        if response := chain.invoke({"query": final_prompt, "context": context}):
            log.info("Router::[RESPONSE] Received from AI: \n%s.", str(response))
            output = self._route(response)
            status = True
            shared.context.forget()
        else:
            output = response

        return status, ProcessorResponse(response=output)

    def _route(self, query: str) -> Optional[str]:
        """Route the actions to the proper function invocations."""
        plain_actions: str = re.sub(r'\d+[.:)-]\s+', '', query)
        actions: list[str] = list(map(str.strip, plain_actions.split(os.linesep)))

        def _execute_plan_() -> Optional[str]:
            """Function responsible for executing the action plan."""
            max_iterations: int = 20
            result: str = ''
            for idx, action in enumerate(actions):
                AskAiEvents.ASKAI_BUS.events.reply.emit(message=f"`[DEBUG] {action}`")
                response: str = features.invoke(action, result)
                if idx > max_iterations or not (result := response):
                    if idx > max_iterations:
                        AskAiEvents.ASKAI_BUS.events.reply_error.emit(message=msg.too_many_actions())
                    break
            return result

        return _execute_plan_()


assert (router := Router().INSTANCE) is not None
