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
from askai.core.enums.acc_response import AccResponse
from askai.core.enums.routing_model import RoutingModel
from askai.core.features.router.task_agent import agent
from askai.core.features.tools.general import final_answer
from askai.core.model.action_plan import ActionPlan
from askai.core.model.ai_reply import AIReply
from askai.core.model.model_result import ModelResult
from askai.core.support.langchain_support import lc_llm
from askai.core.support.rag_provider import RAGProvider
from askai.core.support.shared_instances import shared
from askai.exception.exceptions import InaccurateResponse, InterruptionRequest, TerminatingQuery
from hspylib.core.exception.exceptions import InvalidArgumentError
from hspylib.core.metaclass.singleton import Singleton
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from pathlib import Path
from pydantic_core import ValidationError
from retry import retry
from textwrap import dedent
from typing import Any, Optional, Type, TypeAlias

import logging as log
import os

AgentResponse: TypeAlias = dict[str, Any]


class TaskSplitter(metaclass=Singleton):
    """Processor to provide a divide and conquer set of tasks to fulfill an objective. This is responsible for the
    orchestration and execution of the smaller tasks."""

    INSTANCE: "TaskSplitter"

    HUMAN_PROMPT: str = dedent("""Human Question: '{input}'""").strip()

    # fmt: off
    # Allow the router to retry on the errors bellow.
    RETRIABLE_ERRORS: tuple[Type[Exception], ...] = (
        InaccurateResponse,
        InvalidArgumentError,
        ValidationError
    )  # fmt: on

    @staticmethod
    def wrap_answer(
        query: str, answer: str, model_result: ModelResult = ModelResult.default(), rag: AccResponse | None = None
    ) -> str:
        """Provide a final answer to the user by wrapping the AI response with additional context.
        :param query: The user's question.
        :param answer: The AI's response to the question.
        :param model_result: The result from the selected routing model (default is ModelResult.default()).
        :param rag: The final accuracy check (RAG) response, if available.
        :return: A formatted string containing the final answer.
        """
        output: str = answer
        model: RoutingModel = RoutingModel.of_model(model_result.mid)
        events.reply.emit(reply=AIReply.full(msg.model_select(model)))
        args = {"user": shared.username, "idiom": shared.idiom, "context": answer, "question": query}
        prompt_args: list[str] = [k for k in args.keys()]

        match model, configs.is_speak:
            case RoutingModel.TERMINAL_COMMAND, True:
                output = final_answer("taius-stt", prompt_args, **args)
            case RoutingModel.ASSISTIVE_TECH_HELPER, _:
                output = final_answer("taius-stt", prompt_args, **args)
            case RoutingModel.CHAT_MASTER, _:
                output = final_answer("taius-jarvis", prompt_args, **args)
            case RoutingModel.REFINER, _:
                if rag and rag.reasoning:
                    ctx: str = str(shared.context.flat("HISTORY"))
                    args = {"improvements": rag.reasoning, "context": ctx, "response": answer, "question": query}
                    prompt_args = [k for k in args.keys()]
                    events.reply.emit(reply=AIReply.debug(msg.refine_answer(answer)))
                    output = final_answer("taius-refiner", prompt_args, **args)
            case _:
                # Default is to leave the last AI response intact.
                pass

        shared.context.push("HISTORY", query)
        shared.context.push("HISTORY", output, "assistant")
        shared.memory.save_context({"input": query}, {"output": output})

        return output

    def __init__(self):
        self._approved: bool = False
        self._rag: RAGProvider = RAGProvider("task-splitter.csv")

    def template(self, query: str) -> ChatPromptTemplate:
        """Retrieve the processor Template."""

        evaluation: str = str(shared.context.flat("EVALUATION"))
        template = PromptTemplate(
            input_variables=["os_type", "shell", "datetime", "home", "rag"],
            template=prompt.read_prompt("task-splitter.txt"),
        )
        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    template.format(
                        os_type=prompt.os_type,
                        shell=prompt.shell,
                        datetime=geo_location.datetime,
                        home=Path.home(),
                        rag=self._rag.get_rag_examples(query),
                    ),
                ),
                MessagesPlaceholder("chat_history"),
                ("assistant", evaluation),
                ("human", self.HUMAN_PROMPT),
            ]
        )

    def process(self, question: str, **_) -> Optional[str]:
        """Process the user question by splitting complex tasks into smaller single actionable tasks.
        :param question: The user question to process.
        """

        os.chdir(Path.home())
        shared.context.forget("EVALUATION")  # Erase previous evaluation notes.
        model: ModelResult = ModelResult.default()  # Hard-coding the result model for now.

        @retry(exceptions=self.RETRIABLE_ERRORS, tries=configs.max_router_retries, backoff=1)
        def _process_wrapper() -> Optional[str]:
            """Wrapper to allow accuracy retries."""
            log.info("Router::[QUESTION] '%s'", question)
            runnable = self.template(question) | lc_llm.create_chat_model(Temperature.COLDEST.temp)
            runnable = RunnableWithMessageHistory(
                runnable, shared.context.flat, input_messages_key="input", history_messages_key="chat_history"
            )
            output: str = msg.no_output("task-splitter")

            if response := runnable.invoke({"input": question}, config={"configurable": {"session_id": "HISTORY"}}):
                log.info("Router::[RESPONSE] Received from AI: \n%s.", str(response.content))
                resp_history: list[str] = list()
                plan: ActionPlan = ActionPlan.create(question, response, model)
                events.reply.emit(reply=AIReply.debug(msg.action_plan(str(plan))))
                try:
                    if task_list := plan.tasks:
                        if plan.speak:
                            events.reply.emit(reply=AIReply.detailed(plan.speak))
                        for idx, action in enumerate(task_list, start=1):
                            path_str: str | None = (
                                "Path: " + action.path
                                if hasattr(action, "path") and action.path.upper() not in ["N/A", "NONE"]
                                else None
                            )
                            task: str = f"{action.task}  {path_str or ''}"
                            if output := agent.invoke(task):
                                resp_history.append(output)
                    else:
                        output = plan.speak
                        resp_history.append(output)
                except (InterruptionRequest, TerminatingQuery) as err:
                    output = str(err)
                finally:
                    shared.context.push("HISTORY", question)
            else:
                output = response  # Most of the times, this indicates a failure.

            return output

        return _process_wrapper()


assert (splitter := TaskSplitter().INSTANCE) is not None
