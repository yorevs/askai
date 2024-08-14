#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.features.router
      @file: task_splitter.py
   @created: Mon, 01 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.askai_configs import configs
from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.geo_location import geo_location
from askai.core.engine.openai.temperature import Temperature
from askai.core.features.router.task_agent import agent
from askai.core.model.action_plan import ActionPlan
from askai.core.model.model_result import ModelResult
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.exception.exceptions import InaccurateResponse
from hspylib.core.exception.exceptions import InvalidArgumentError
from hspylib.core.metaclass.singleton import Singleton
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from pathlib import Path
from retry import retry
from textwrap import dedent
from typing import Any, Optional, Type, TypeAlias

import logging as log
import os
import PIL

AgentResponse: TypeAlias = dict[str, Any]


class TaskSplitter(metaclass=Singleton):
    """Processor to provide a divide and conquer set of tasks to fulfill an objective. This is responsible for the
    orchestration and execution of the smaller tasks."""

    INSTANCE: "TaskSplitter"

    HUMAN_PROMPT: str = dedent("""Human Question: '{input}'""").strip()

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
    def template(self) -> ChatPromptTemplate:
        """Retrieve the processor Template."""

        rag: str = str(shared.context.flat("EVALUATION"))
        template = PromptTemplate(
            input_variables=["os_type", "shell", "datetime", "home"], template=prompt.read_prompt("task-split.txt")
        )
        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    template.format(
                        os_type=prompt.os_type, shell=prompt.shell,
                        datetime=geo_location.datetime, home=Path.home()
                    ),
                ),
                MessagesPlaceholder("chat_history"),
                ("assistant", rag),
                ("human", self.HUMAN_PROMPT),
            ]
        )

    def process(self, question: str, **_) -> Optional[str]:
        """Process the user question by splitting complex tasks into smaller single actionable tasks.
        :param question: The user question to process.
        """

        os.chdir(Path.home())
        shared.context.forget("EVALUATION")  # Erase previous scratchpad.
        model: ModelResult = ModelResult.default()  # Hard-coding the result model for now.

        @retry(exceptions=self.RETRIABLE_ERRORS, tries=configs.max_router_retries, backoff=0)
        def _process_wrapper() -> Optional[str]:
            """Wrapper to allow accuracy retries."""
            log.info("Router::[QUESTION] '%s'", question)
            runnable = self.template | lc_llm.create_chat_model(Temperature.CODE_GENERATION.temp)
            runnable = RunnableWithMessageHistory(
                runnable, shared.context.flat, input_messages_key="input", history_messages_key="chat_history"
            )
            if response := runnable.invoke({"input": question}, config={"configurable": {"session_id": "HISTORY"}}):
                log.info("Router::[RESPONSE] Received from AI: \n%s.", str(response.content))
                plan: ActionPlan = ActionPlan.create(question, response, model)
                events.reply.emit(message=msg.action_plan(str(plan)), verbosity="debug")
                output = agent.invoke(question, plan)
            else:
                # Most of the times, this indicates a failure.
                output = response
            return output

        return _process_wrapper()


assert (splitter := TaskSplitter().INSTANCE) is not None
