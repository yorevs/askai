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
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder
from retry import retry

from askai.core.askai_configs import configs
from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperature import Temperature
from askai.core.features.actions import features
from askai.core.features.tools.analysis import assert_accuracy
from askai.core.features.tools.general import final_answer
from askai.core.model.action_plan import ActionPlan
from askai.core.support.langchain_support import lc_llm
from askai.core.support.object_mapper import object_mapper
from askai.core.support.shared_instances import shared
from askai.exception.exceptions import InaccurateResponse

AgentResponse: TypeAlias = dict[str, Any]


class Router(metaclass=Singleton):
    """Class to provide a divide and conquer set of actions to fulfill an objective. This is responsible for the
    orchestration and execution of the actions."""

    INSTANCE: "Router"

    HUMAN_PROMPT: str = "{input}\n (reminder to respond in a JSON blob no matter what)"

    def __init__(self):
        self._approved = False

    @property
    def router_template(self) -> ChatPromptTemplate:
        template = PromptTemplate(input_variables=["os_type", "user"], template=prompt.read_prompt("router.txt"))
        return ChatPromptTemplate.from_messages(
            [
                ("system", template.format(os_type=prompt.os_type, user=prompt.user)),
                MessagesPlaceholder("chat_history", optional=True),
                ("human", self.HUMAN_PROMPT),
            ]
        )

    @property
    def agent_template(self) -> ChatPromptTemplate:
        return prompt.hub("hwchase17/structured-chat-agent")

    def process(self, query: str) -> Optional[str]:
        """Process the user query and retrieve the final response.
        :param query: The user query to complete.
        """
        @retry(exceptions=InaccurateResponse, tries=configs.max_router_retries, backoff=0)
        def _process_wrapper() -> Optional[str]:
            """Wrapper to allow RAG retries."""
            log.info("Router::[QUESTION] '%s'", query)
            runnable = self.router_template | lc_llm.create_chat_model(Temperature.COLDEST.temp)
            response = runnable.invoke({"input": query})
            if response:
                log.info("Router::[RESPONSE] Received from AI: \n%s.", str(response))
                plan: ActionPlan = object_mapper.of_json(response.content, ActionPlan)
                if not isinstance(plan, ActionPlan):
                    return f"Error: AI responded an invalid JSON object -> {str(plan)}"
                AskAiEvents.ASKAI_BUS.events.reply.emit(
                    message=msg.action_plan(f"[{plan.category.upper()}] {plan.reasoning}"),
                    verbosity="debug"
                )
                output = self._route(query, plan)
            else:
                output = response
            return output

        return _process_wrapper()

    def _route(self, query: str, action_plan: ActionPlan) -> str:
        """Route the actions to the proper function invocations.

        :param query: The user query to complete.
        """
        last_response: str = ''
        actions: list[str] = action_plan.plan
        for action in actions:
            task = ', '.join([f"{k.title()}: {v}" for k, v in vars(action).items()])
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=f"> `{action}`", verbosity="debug")
            llm = lc_llm.create_chat_model(Temperature.COLDEST.temp)
            chat_memory = shared.create_chat_memory()
            lc_agent = create_structured_chat_agent(llm, features.agent_tools(), self.agent_template)
            agent = AgentExecutor(
                agent=lc_agent, tools=features.agent_tools(),
                max_iteraction=configs.max_router_retries,
                memory=chat_memory,
                max_execution_time=30,
                handle_parsing_errors=True,
                return_only_outputs=True,
                early_stopping_method=True,
                verbose=configs.is_debug,
            )
            if (response := agent.invoke({"input": task})) and (output := response['output']):
                log.info("Router::[RESPONSE] Received from AI: \n%s.", output)
                last_response = output
                assert_accuracy(query,  output)
                continue
            raise InaccurateResponse("AI provided AN EMPTY response")

        return self._wrap_answer(query, action_plan.category, msg.translate(last_response))

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
