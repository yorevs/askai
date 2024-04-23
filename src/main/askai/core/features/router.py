#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.features.router
      @file: router.py
   @created: Mon, 01 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""

import logging as log
from typing import Optional, TypeAlias, Any

from hspylib.core.metaclass.singleton import Singleton
from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from retry import retry

from askai.core.askai_configs import configs
from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.features.actions import features
from askai.core.features.tools.analysis import assert_accuracy
from askai.core.features.tools.general import final_answer
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.exception.exceptions import InaccurateResponse

AgentResponse: TypeAlias = dict[str, Any]


class Router(metaclass=Singleton):
    """Class to provide a divide and conquer set of actions to fulfill an objective. This is responsible for the
    orchestration and execution of the actions."""

    INSTANCE: "Router"

    HUMAN_PROMPT: str = "{input}\n\n{agent_scratchpad}\n (reminder to respond in a JSON blob no matter what)"

    def __init__(self):
        self._approved = False

    @property
    def template(self) -> str:
        return prompt.read_prompt("router.txt")

    def process(self, query: str) -> Optional[str]:
        """Process the user query and retrieve the final response.
        :param query: The user query to complete.
        """

        @retry(exceptions=InaccurateResponse, tries=configs.max_router_retries, backoff=0)
        def _process_wrapper() -> Optional[str]:
            """Wrapper to allow RAG retries."""
            template: PromptTemplate = PromptTemplate(
                input_variables=["os_type", "user"], template=prompt.read_prompt("router.txt"))
            system_prompt: str = template.format(os_type=prompt.os_type, user=prompt.user)
            router_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    MessagesPlaceholder("chat_history", optional=True),
                    ("human", self.HUMAN_PROMPT),
                ]
            )
            llm = lc_llm.create_chat_model()
            chat_memory = shared.create_chat_memory()
            lc_agent = create_structured_chat_agent(llm, features.agent_tools(), router_prompt)
            agent = AgentExecutor(
                agent=lc_agent, tools=features.agent_tools(),
                verbose=True, max_iteraction=configs.max_router_retries,
                memory=chat_memory,
                handle_parsing_errors=True,
            )
            response: AgentResponse = agent.invoke({"input": query})
            if response and (output := response['output']):
                reasoning: str = response['reasoning'] if 'reasoning' in response else 'other'
                category: str = response['category'] if 'category' in response else 'other'
                log.info("Router::[RESPONSE] Received from AI: \n%s.", output)
                AskAiEvents.ASKAI_BUS.events.reply.emit(
                    message=msg.action_plan(f"[{category.upper()}] {reasoning}"),
                    verbosity="debug")
                assert_accuracy(query, output)
                return self._wrap_answer(query, category, msg.translate(output))
            raise InaccurateResponse("AI provided AN EMPTY response")

        return _process_wrapper()

    def _wrap_answer(self, question: str, category: str, response: str) -> str:
        """Provide a final answer to the user.
        :param question: The user question.
        :param response: The AI response.
        """
        match category.lower(), configs.is_speak:
            case "chat", False:
                return final_answer(question, context=response)
            case "file system", True:
                return final_answer(question, persona_prompt='stt', context=response)
            case _:
                return response


assert (router := Router().INSTANCE) is not None
