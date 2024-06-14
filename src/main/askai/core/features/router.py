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
import re
from pathlib import Path
from textwrap import dedent
from typing import Any, Optional, Type, TypeAlias

import PIL
from hspylib.core.exception.exceptions import InvalidArgumentError
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_state
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from retry import retry

from askai.core.askai_configs import configs
from askai.core.askai_events import AskAiEvents
from askai.core.askai_prompt import prompt
from askai.core.component.geo_location import geo_location
from askai.core.engine.openai.temperature import Temperature
from askai.core.features.router_agent import agent
from askai.core.model.action_plan import ActionPlan
from askai.core.model.model_result import ModelResult
from askai.core.model.routing_model import RoutingModel
from askai.core.support.langchain_support import lc_llm
from askai.core.support.object_mapper import object_mapper
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import extract_codeblock
from askai.exception.exceptions import InaccurateResponse

AgentResponse: TypeAlias = dict[str, Any]


class Router(metaclass=Singleton):
    """Processor to provide a divide and conquer set of tasks to fulfill an objective. This is responsible for the
    orchestration and execution of the smaller tasks."""

    INSTANCE: "Router"

    HUMAN_PROMPT: str = dedent(
        """
        (reminder to respond in a strict JSON no matter what).
        ---
        Human Question: "{input}"

        Answer:
        """
    )

    # Allow the router to retry on the errors bellow.
    RETRIABLE_ERRORS: tuple[Type[Exception], ...] = (
        InaccurateResponse,
        InvalidArgumentError,
        ValueError,
        AttributeError,
        PIL.UnidentifiedImageError,
    )

    def __init__(self):
        self._approved: bool = False

    @property
    def router_template(self) -> ChatPromptTemplate:
        """Retrieve the Router Template."""
        rag: str = str(shared.context.flat("RAG"))
        template = PromptTemplate(
            input_variables=["os_type", "shell", "datetime", "home"], template=prompt.read_prompt("task-split.txt")
        )
        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    template.format(
                        os_type=prompt.os_type, shell=prompt.shell, datetime=geo_location.datetime, home=Path.home()
                    ),
                ),
                MessagesPlaceholder("chat_history", optional=True),
                ("assistant", rag),
                ("human", self.HUMAN_PROMPT),
            ]
        )

    @property
    def model_template(self) -> str:
        """Retrieve the Routing Model Template."""
        template = PromptTemplate(input_variables=["models"], template=prompt.read_prompt("model-select.txt"))
        return template.format(models=RoutingModel.enlist())

    @staticmethod
    def _parse_response(response: str) -> ActionPlan:
        """Parse the router response.
        :param response: The router response. This should be a JSON blob, but sometimes the AI responds with a
        straight JSON string.
        """
        json_string = response
        if re.match(r"^`{3}(.+)`{3}$", response):
            _, json_string = extract_codeblock(response)
        plan: ActionPlan = object_mapper.of_json(json_string, ActionPlan)
        if not isinstance(plan, ActionPlan):
            raise InaccurateResponse(f"AI responded an invalid JSON blob -> {str(plan)}")

        return plan

    def _select_model(self) -> ModelResult:
        """Select the response model."""
        llm = lc_llm.create_chat_model(Temperature.DATA_ANALYSIS.temp)
        if response := llm.invoke(self.model_template):
            json_string: str = response.content  # from AIMessage
            model_result: ModelResult | str = object_mapper.of_json(json_string, ModelResult)
            model_result: ModelResult = model_result \
                if isinstance(model_result, ModelResult) \
                else ModelResult.default()
        else:
            model_result: ModelResult = ModelResult.default()

        return model_result

    def process(self, query: str) -> Optional[str]:
        """Process the user query and retrieve the final response.
        :param query: The user query to complete.
        """

        model: ModelResult = self._select_model()

        @retry(exceptions=self.RETRIABLE_ERRORS, tries=configs.max_router_retries, backoff=0)
        def _process_wrapper() -> Optional[str]:
            """Wrapper to allow RAG retries."""
            log.info("Router::[QUESTION] '%s'", query)
            runnable = self.router_template | lc_llm.create_chat_model(Temperature.COLDEST.temp)
            runnable = RunnableWithMessageHistory(
                runnable, shared.context.flat, input_messages_key="input", history_messages_key="chat_history"
            )
            if response := runnable.invoke({"input": query}, config={"configurable": {"session_id": "HISTORY"}}):
                log.info("Router::[RESPONSE] Received from AI: \n%s.", str(response.content))
                plan: ActionPlan = self._parse_response(response.content)
                check_state(plan is not None and isinstance(plan, ActionPlan),
                            f"Invalid action plan received from LLM: {type(plan)}")
                plan.model = model
                AskAiEvents.ASKAI_BUS.events.reply.emit(message=f"> {plan}", verbosity="debug")
                output = agent.invoke(query, plan) if plan.tasks else agent.wrap_answer(query, plan.speak)
            else:
                # Most of the times, this represents a failure.
                output = response
            return output

        return _process_wrapper()


assert (router := Router().INSTANCE) is not None
