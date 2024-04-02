import json
import logging as log
import os
from functools import lru_cache
from operator import itemgetter
from typing import TypeAlias, Tuple, Optional

from hspylib.core.metaclass.singleton import Singleton
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.output_parsers import JsonOutputToolsParser
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda, RunnablePassthrough
from langchain_core.runnables.utils import Input, Output
from langchain_core.tools import tool

from askai.__classpath__ import classpath
from askai.core.askai_prompt import prompt
from askai.core.component.geo_location import geo_location
from askai.core.model.processor_response import ProcessorResponse
from askai.core.processor.tools.analysis import analyze_output
from askai.core.processor.tools.summarizer import summarize
from askai.core.processor.tools.terminal import terminal
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared

RunnableTool: TypeAlias = Runnable[list[Input], list[Output]]


class Router(metaclass=Singleton):
    """TODO"""

    INSTANCE: 'Router' = None

    PROMPT_DIR: str = str(classpath.resource_path()) + "/assets/prompts/v4"

    IS_TERMINATING: bool = None

    IS_INTELLIGIBLE: bool = None

    @staticmethod
    @tool
    def intelligible(question: str) -> str:
        """Indicate that the question is unclear or not understandable."""
        print(f"Question: '{question}' is not intelligible.")
        Router.IS_INTELLIGIBLE = False
        return question

    @staticmethod
    @tool
    def terminating(reason: str) -> str:
        """Indicate that the user intends to end the conversation."""
        print(reason)
        Router.IS_TERMINATING = True
        return reason

    def __init__(self):
        self._approved = False
        self.tools = [
            terminal, analyze_output, summarize,
            self.intelligible, self.terminating
        ]

    @lru_cache
    def template(self) -> str:
        return prompt.read_prompt("router-prompt.txt", self.PROMPT_DIR)

    def human_approval(self, tool_invocations: list) -> list:
        """TODO"""
        tool_strs = "\n\n".join(
            json.dumps(tool_call, indent=2) for tool_call in tool_invocations
        )
        msg = (
            f"Do you approve of the following tool invocations\n\n{tool_strs}\n\n"
            "Anything except 'Y'/'Yes' (case-insensitive) will be treated as a no."
        )
        if (resp := input(msg).lower()) not in ("yes", "y"):
            raise ValueError(f"Tool invocations not approved:\n\n{tool_strs}")
        self._approved = True
        return tool_invocations

    def process(self, question: str) -> Tuple[bool, ProcessorResponse]:
        status = False
        self.IS_TERMINATING: bool = False
        self.IS_INTELLIGIBLE: bool = True
        template = PromptTemplate(input_variables=[
            'os_type', 'shell', 'idiom', 'location', 'datetime'
        ], template=self.template())
        final_prompt = template.format(
            os_type=prompt.os_type, shell=prompt.shell, idiom=shared.idiom,
            location=geo_location.location, datetime=geo_location.datetime
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

    def _call_tool(self, tool_invocation: dict) -> Runnable:
        """Function for dynamically constructing the end of the chain based on the model-selected tool."""
        tool_map = {tool.name: tool for tool in self.tools}
        tool = tool_map[tool_invocation["type"]]
        return RunnablePassthrough.assign(output=itemgetter("args") | tool)

    def _route(self, query: str) -> Optional[None]:
        """Route the actions to the proper processors."""
        result = None
        actions: list[str] = query.split(os.linesep)
        for action in actions:
            call_tool_list = RunnableLambda(self._call_tool).map()
            # fmt: off
            chain = lc_llm.create_chat_model().bind_tools(self.tools) | JsonOutputToolsParser() | call_tool_list
            response: Output = chain.invoke(action)
            result = response[0]['output']
            # fmt: on
        return result


assert (router := Router().INSTANCE) is not None
