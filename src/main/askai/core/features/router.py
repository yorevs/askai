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
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from retry import retry

from askai.core.askai_configs import configs
from askai.core.askai_events import AskAiEvents
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperature import Temperature
from askai.core.features.structured_agent import agent
from askai.core.model.action_plan import ActionPlan
from askai.core.model.category import Category
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

    HUMAN_PROMPT: str = dedent("""
    {input}

    (reminder to respond in a JSON blob and to use at least one action, no matter what).
    """)

    # Allow the router to retry on the errors bellow.
    RETRIABLE_ERRORS: tuple[Type[Exception], ...] = (
        InaccurateResponse,
        ValueError,
        AttributeError,
        InvalidArgumentError,
        PIL.UnidentifiedImageError,
    )

    def __init__(self):
        self._approved: bool = False

    @property
    def router_template(self) -> ChatPromptTemplate:
        """Retrieve the Router Template."""
        scratchpad: str = str(shared.context.flat("SCRATCHPAD"))
        template = PromptTemplate(
            input_variables=[
                "home", "categories"
            ], template=prompt.read_prompt("router.txt")
        )
        return ChatPromptTemplate.from_messages(
            [
                ("system", template.format(home=Path.home(), categories=Category.template())),
                MessagesPlaceholder("chat_history", optional=True),
                ("assistant", scratchpad),
                ("human", self.HUMAN_PROMPT),
            ]
        )

    def process(self, query: str) -> Optional[str]:
        """Process the user query and retrieve the final response.
        :param query: The user query to complete.
        """

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
                    raise InaccurateResponse(f"AI responded an invalid JSON blob -> {str(plan)}")
                if not plan.actions:
                    plan.category = plan.category if hasattr(plan, 'category') else Category.FINAL_ANSWER.value
                    plan.ultimate_goal = plan.ultimate_goal if hasattr(plan, 'ultimate_goal') else query
                    plan.actions = [SimpleNamespace(task=f"Answer the human: {query}")]
                if hasattr(plan, 'thoughts') and hasattr(plan.thoughts, 'speak'):
                    AskAiEvents.ASKAI_BUS.events.reply.emit(message=plan.thoughts.speak)
                output = agent.invoke(query, plan)
            else:
                output = response
            return output

        return _process_wrapper()


assert (router := Router().INSTANCE) is not None
