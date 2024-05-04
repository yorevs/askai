#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.features.router
      @file: router.py
   @created: Mon, 01 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import logging as log
from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace
from typing import Any, Optional, Type, TypeAlias

import PIL
from hspylib.core.exception.exceptions import InvalidArgumentError
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_argument
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain.memory.chat_memory import BaseChatMemory
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain_core.runnables.history import RunnableWithMessageHistory
from retry import retry

from askai.core.askai_configs import configs
from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperature import Temperature
from askai.core.features.actions import features
from askai.core.features.rag.commons import final_answer, assert_accuracy
from askai.core.model.action_plan import ActionPlan
from askai.core.support.langchain_support import lc_llm
from askai.core.support.object_mapper import object_mapper
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import extract_codeblock
from askai.exception.exceptions import InaccurateResponse

AgentResponse: TypeAlias = dict[str, Any]


class Router(metaclass=Singleton):
    """Class to provide a divide and conquer set of actions to fulfill an objective. This is responsible for the
    orchestration and execution of the actions."""

    INSTANCE: "Router"

    HUMAN_PROMPT: str = dedent(
        """
    Answer my question in the end.\n(reminder to respond in a JSON blob no matter what)\nQuestion: '{input}'
    """
    )

    # Allow the router to retry on the errors bellow.
    RETRIABLE_ERRORS: tuple[Type[Exception], ...] = (
        InaccurateResponse,
        ValueError,
        AttributeError,
        InvalidArgumentError,
        PIL.UnidentifiedImageError,
    )

    @staticmethod
    def _wrap_answer(question: str, category: str, response: str) -> str:
        """Provide a final answer to the user.
        :param question: The user question.
        :param response: The AI response.
        """
        match category.lower(), configs.is_speak:
            case "final answer" | "general chat" | "image caption", _:
                response = final_answer(question, context=response)
            case "file management", True:
                response = final_answer(question, persona_prompt="stt", context=response)
            case "technical assistance", _:
                response = final_answer(question, persona_prompt="stt", context=response)

        return response

    def __init__(self):
        self._approved = False

    @property
    def router_template(self) -> ChatPromptTemplate:
        """Retrieve the Router Template."""
        template = PromptTemplate(
            input_variables=["home", "scratchpad"], template=prompt.read_prompt("router.txt")
        )
        return ChatPromptTemplate.from_messages(
            [
                ("system", template.format(home=Path.home())),
                MessagesPlaceholder("chat_history", optional=True),
                ("human", self.HUMAN_PROMPT),
            ]
        )

    @property
    def agent_template(self) -> ChatPromptTemplate:
        """Retrieve the Structured Agent Template."""
        return prompt.hub("hwchase17/structured-chat-agent")

    def process(self, query: str) -> Optional[str]:
        """Process the user query and retrieve the final response.
        :param query: The user query to complete.
        """

        agent = self._create_agent()

        @retry(exceptions=self.RETRIABLE_ERRORS, tries=configs.max_router_retries, backoff=0)
        def _process_wrapper() -> Optional[str]:
            """Wrapper to allow RAG retries."""
            log.info("Router::[QUESTION] '%s'", query)
            runnable = self.router_template | lc_llm.create_chat_model(Temperature.CODE_GENERATION.temp)
            runnable = RunnableWithMessageHistory(
                runnable,
                shared.context.flat,
                input_messages_key="input",
                history_messages_key="chat_history",
            )
            if response := runnable.invoke({"input": query}, config={"configurable": {"session_id": "HISTORY"}}):
                log.info("Router::[RESPONSE] Received from AI: \n%s.", str(response))
                _, json_string = extract_codeblock(response.content)
                plan: ActionPlan = object_mapper.of_json(json_string, ActionPlan)
                if not isinstance(plan, ActionPlan):
                    raise InaccurateResponse(f"AI responded an invalid JSON object -> {str(plan)}")
                AskAiEvents.ASKAI_BUS.events.reply.emit(
                    message=f"- **{plan.category}**: `{plan.reasoning}`", verbosity="debug")
                output = self._route(agent, query, plan)
            else:
                output = response
            return output

        return _process_wrapper()

    def _route(self, agent: Runnable, query: str, action_plan: ActionPlan) -> str:
        """Route the actions to the proper function invocations.
        :param query: The user query to complete.
        :param action_plan: The action plan to resolve the request.
        """
        last_response: str = ""
        actions: list[SimpleNamespace] = action_plan.plan
        check_argument(all(isinstance(act, SimpleNamespace) for act in actions), "Invalid action format")
        for action in actions:
            task = ", ".join([f"{k.title()}: {v}" for k, v in vars(action).items()])
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=f"> `{task}`", verbosity="debug")
            if (response := agent.invoke({"input": task})) and (output := response["output"]):
                log.info("Router::[RESPONSE] Received from AI: \n%s.", output)
                last_response = output
                assert_accuracy(action.action, output)
                continue
            raise InaccurateResponse("AI provided AN EMPTY response")

        return self._wrap_answer(query, action_plan.category, msg.translate(last_response))

    def _create_agent(self) -> Runnable:
        """TODO"""
        llm = lc_llm.create_chat_model(Temperature.COLDEST.temp)
        chat_memory = self._create_chat_memory()
        lc_agent = create_structured_chat_agent(llm, features.agent_tools(), self.agent_template)
        return AgentExecutor(
            agent=lc_agent,
            tools=features.agent_tools(),
            max_iteraction=configs.max_router_retries,
            memory=chat_memory,
            max_execution_time=configs.max_agent_execution_time_seconds,
            handle_parsing_errors=True,
            return_only_outputs=True,
            early_stopping_method=True,
            verbose=configs.is_debug,
        )

    def _create_chat_memory(self) -> BaseChatMemory:
        """TODO"""
        return ConversationBufferWindowMemory(
            memory_key="chat_history", k=configs.max_chat_history_size, return_messages=True)


assert (router := Router().INSTANCE) is not None
