import logging as log
import os
from functools import lru_cache
from typing import TypeAlias, Tuple, Optional

from hspylib.core.metaclass.singleton import Singleton
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.runnables.utils import Input, Output

from askai.__classpath__ import classpath
from askai.core.askai_events import AskAiEvents
from askai.core.askai_prompt import prompt
from askai.core.component.geo_location import geo_location
from askai.core.model.processor_response import ProcessorResponse
from askai.core.processor.processor_base import AIProcessor
from askai.core.processor.processor_factory import ProcessorFactory
from askai.core.processor.processor_proxy import proxy
from askai.core.support.langchain_support import lc_llm
from askai.core.support.object_mapper import object_mapper
from askai.core.support.shared_instances import shared

RunnableTool: TypeAlias = Runnable[list[Input], list[Output]]


class Router(metaclass=Singleton):
    """TODO"""

    INSTANCE: 'Router' = None

    PROMPT_DIR: str = str(classpath.resource_path()) + "/assets/prompts/v4"


    @lru_cache
    def template(self) -> str:
        return prompt.read_prompt("router-prompt.txt", self.PROMPT_DIR)

    def process(self, question: str) -> Tuple[bool, ProcessorResponse]:
        status = False
        template = PromptTemplate(input_variables=[
            'os_type', 'shell', 'idiom', 'location', 'datetime'
        ], template=self.template())
        final_prompt = template.format(
            os_type=prompt.os_type, shell=prompt.shell, idiom=shared.idiom,
            location=geo_location.location, datetime=geo_location.datetime,
            question=question
        )
        shared.context.set("SETUP", final_prompt, "system")
        shared.context.set("QUESTION", f"\n\nQuestion: {question}\n\nHelpful Answer:")
        ctx: str = shared.context.flat("CONTEXT", "SETUP", "QUESTION")
        log.info("Router::[QUESTION] '%s'  context=%s", question, ctx)

        chat_prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
        chain = create_stuff_documents_chain(lc_llm.create_chat_model(), chat_prompt)
        context = Document(ctx)

        if response := chain.invoke({"query": question, "context": [context]}):
            log.info("Router::[RESPONSE] Received from AI: %s.", str(response))
            if output := self._route(response):
                shared.context.push("CONTEXT", f"\n\nUser:\n{question}")
            status = True
        else:
            output = ProcessorResponse(question=question, terminating=True, response=response)

        return status, output

    def _route(self, query: str) -> Optional[str]:
        """Route the actions to the proper processors."""
        output = None
        actions: list[str] = query.split(os.linesep)
        for action in actions:
            status, response = proxy.process(action)
            output = response
            while status and output and isinstance(output, ProcessorResponse):
                processor: AIProcessor = ProcessorFactory.find_processor(output.query_type)
                status, response = processor.process(output)
                if status and response and processor.next_in_chain():
                    mapped_response = object_mapper.of_json(output, ProcessorResponse)
                    if isinstance(mapped_response, ProcessorResponse):
                        output = mapped_response
                        continue
                    else:
                        output = str(mapped_response)
                else:
                    AskAiEvents.ASKAI_BUS.events.reply.emit(message=response)
                    output = None

        return output


assert (router := Router().INSTANCE) is not None
