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
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain_core.runnables.history import RunnableWithMessageHistory
from retry import retry

from askai.core.askai_configs import configs
from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import cache
from askai.core.engine.openai.temperature import Temperature
from askai.core.features.actions import features
from askai.core.features.rag.rag import final_answer, assert_accuracy
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
    def _assert_and_store(action: str, output: str) -> None:
        """TODO"""
        assert_accuracy(action, output)
        shared.context.push("HISTORY", action, "assistant")
        shared.context.push("HISTORY", output, "assistant")

    @staticmethod
    def _wrap_answer(query: str, category: str, response: str) -> str:
        """Provide a final answer to the user.
        :param query: The user question.
        :param response: The AI response.
        """
        output: str = response
        match category.lower(), configs.is_speak:
            case "file management", True:
                output = final_answer(query, persona_prompt="stt", context=response)
            case "assistive requests", _:
                output = final_answer(query, persona_prompt="stt", context=response)
            case "image caption" | "general chat", _:
                output = final_answer(query, context=response)

        shared.context.push("HISTORY", query)
        shared.context.push("HISTORY", output, "assistant")
        cache.save_reply(query, output)

        return output

    def __init__(self):
        self._approved: bool = False
        self._agent: Runnable | None = None

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

        if self._agent is None:
            self._agent = self._create_agent()

        @retry(exceptions=self.RETRIABLE_ERRORS, tries=configs.max_router_retries, backoff=0)
        def _process_wrapper() -> Optional[str]:
            """Wrapper to allow RAG retries."""
            log.info("Router::[QUESTION] '%s'", query)
            runnable = self.router_template | lc_llm.create_chat_model(Temperature.CODE_COMMENT_GENERATION.temp)
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
                output = self._route(self._agent, query, plan)
            else:
                output = response
            return output

        return _process_wrapper()

    def _route(self, agent: Runnable, query: str, action_plan: ActionPlan) -> str:
        """Route the actions to the proper function invocations.
        :param query: The user query to complete.
        :param action_plan: The action plan to resolve the request.
        """
        output: str = ""
        actions: list[SimpleNamespace] = action_plan.plan
        check_argument(all(isinstance(act, SimpleNamespace) for act in actions), "Invalid action format")

        for action in actions:
            task = ", ".join([f"{k.title()}: {v}" for k, v in vars(action).items()])
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=f"> {task}", verbosity="debug")
            if action_plan.is_final() and (output := action.action):
                log.info("Router::[RESPONSE] Action is a final answer from AI: \n%s.", output)
                self._assert_and_store(action.action, output)
                break
            elif (response := agent.invoke({"input": task})) and (output := response["output"]):
                log.info("Router::[RESPONSE] Received from AI: \n%s.", output)
                self._assert_and_store(action.action, output)
                continue

            raise InaccurateResponse("AI provided AN EMPTY response")

        # Provide a final RAG check to ensure the question has been accurately responded.
        assert_accuracy(query, output)

        return self._wrap_answer(query, action_plan.category, msg.translate(output))

    def _create_agent(self) -> Runnable:
        """TODO"""
        llm = lc_llm.create_chat_model(Temperature.CODE_GENERATION.temp)
        chat_memory = ConversationBufferWindowMemory(
            memory_key="chat_history", k=configs.max_chat_history_size, return_messages=True)
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


assert (router := Router().INSTANCE) is not None
