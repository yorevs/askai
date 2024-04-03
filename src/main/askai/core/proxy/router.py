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
from askai.core.askai_prompt import prompt
from askai.core.component.geo_location import geo_location
from askai.core.model.processor_response import ProcessorResponse
from askai.core.proxy.features import features
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared

RunnableTool: TypeAlias = Runnable[list[Input], list[Output]]


class Router(metaclass=Singleton):
    """TODO"""

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
        ctx: str = shared.context.flat("CONTEXT", "INTERNET")
        log.info("Router::[QUESTION] '%s'  context: '%s'", question, ctx)
        chat_prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
        chain = create_stuff_documents_chain(lc_llm.create_chat_model(), chat_prompt)
        context = [Document(ctx)]

        if response := chain.invoke({"query": final_prompt, "context": context}):
            log.info("Router::[RESPONSE] Received from AI: %s.", str(response))
            output = self._route(response)
            status = True
        else:
            output = response

        return status, ProcessorResponse(response=output)

    def _route(self, query: str) -> Optional[str]:
        """Route the actions to the proper function invocations."""
        max_actions: int = 20
        result = shared.context.flat("CONTEXT", "GENERAL")
        actions: list[str] = re.sub(r'\d+[.:)-]\s+', '', query).split(os.linesep)
        for idx, action in enumerate(actions):
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=f"`{action}`")
            response: str = features.invoke(action, result)
            if idx > max_actions or not (result := response):
                break
        return result


assert (router := Router().INSTANCE) is not None
