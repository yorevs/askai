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
import logging as log
import os
from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace
from typing import Any, Optional, Type, TypeAlias

from askai.core.askai_configs import configs
from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.geo_location import geo_location
from askai.core.engine.openai.temperature import Temperature
from askai.core.enums.acc_color import AccColor
from askai.core.enums.response_model import ResponseModel
from askai.core.features.router.agent_tools import features
from askai.core.features.router.evaluation import assert_accuracy
from askai.core.features.router.task_agent import agent
from askai.core.features.tools.general import final_answer
from askai.core.model.acc_response import AccResponse
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
from pydantic_core import ValidationError
from retry import retry

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
        query: str,
        answer: str,
        model_result: ModelResult = ModelResult.default(),
        acc_response: AccResponse | None = None,
    ) -> str:
        """Provide a final answer to the user by wrapping the AI response with additional context.
        :param query: The user's question.
        :param answer: The AI's response to the question.
        :param model_result: The result from the selected routing model (default is ModelResult.default()).
        :param acc_response: The final accuracy response, if available.
        :return: A formatted string containing the final answer.
        """
        output: str = answer
        args = {"user": prompt.user.title(), "idiom": shared.idiom, "context": answer, "question": query}
        prompt_args: list[str] = [k for k in args.keys()]
        model: ResponseModel = (
            ResponseModel.REFINER
            if acc_response and (acc_response.acc_color > AccColor.GOOD)
            else ResponseModel.of_model(model_result.mid)
        )
        events.reply.emit(reply=AIReply.full(msg.model_select(model)))

        match model, configs.is_speak:
            case ResponseModel.TERMINAL_COMMAND, True:
                output = final_answer("taius-stt", prompt_args, **args)
            case ResponseModel.ASSISTIVE_TECH_HELPER, _:
                output = final_answer("taius-stt", prompt_args, **args)
            case ResponseModel.CHAT_MASTER, _:
                output = final_answer("taius-jarvis", prompt_args, **args)
            case ResponseModel.REFINER, _:
                if acc_response and acc_response.reasoning:
                    ctx: str = str(shared.context.flat("HISTORY"))
                    args = {"improvements": acc_response.details, "context": ctx, "response": answer, "question": query}
                    prompt_args = [k for k in args.keys()]
                    events.reply.emit(reply=AIReply.debug(msg.refine_answer(answer)))
                    output = final_answer("taius-refiner", prompt_args, **args)
            case _:
                pass  # Default is to leave the last AI response as is

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
            input_variables=["os_type", "shell", "datetime", "home", "agent_tools", "rag"],
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
                        agent_tools=features.available_tools,
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
        log.info("Router::[QUESTION] '%s'", question)

        @retry(exceptions=self.RETRIABLE_ERRORS, tries=configs.max_router_retries, backoff=1, jitter=1)
        def _splitter_wrapper_() -> Optional[str]:
            # Invoke the LLM to split the tasks and create an action plan.
            runnable = self.template(question) | lc_llm.create_chat_model(Temperature.COLDEST.temp)
            runnable = RunnableWithMessageHistory(
                runnable, shared.context.flat, input_messages_key="input", history_messages_key="chat_history"
            )

            if response := runnable.invoke({"input": question}, config={"configurable": {"session_id": "HISTORY"}}):
                log.info("Router::[RESPONSE] Received from AI: \n%s.", str(response.content))
                plan = ActionPlan.create(question, response, model)
                if task_list := plan.tasks:
                    events.reply.emit(reply=AIReply.debug(msg.action_plan(str(plan))))
                    if plan.speak:
                        events.reply.emit(reply=AIReply.info(plan.speak))
                else:
                    # Most of the times, indicates the LLM responded directly.
                    acc_response: AccResponse = assert_accuracy(question, response, AccColor.GOOD)
                    if output := plan.speak:
                        shared.context.push("HISTORY", question)
                        shared.context.push("HISTORY", output, "assistant")
                    else:
                        output = msg.no_output("Task-Splitter")
                    return self.wrap_answer(question, output, plan.model, acc_response)
            else:
                return response  # Most of the times, indicates a failure.

            try:
                agent_output = self._process_tasks(task_list)
                acc_response: AccResponse = assert_accuracy(question, agent_output, AccColor.MODERATE)
            except (InterruptionRequest, TerminatingQuery) as err:
                return str(err)
            except self.RETRIABLE_ERRORS:
                events.reply.emit(reply=AIReply.error(msg.sorry_retry()))
                raise

            return self.wrap_answer(question, agent_output, plan.model, acc_response)

        return _splitter_wrapper_()

    @retry(exceptions=RETRIABLE_ERRORS, tries=configs.max_router_retries, backoff=1, jitter=1)
    def _process_tasks(self, task_list: list[SimpleNamespace]) -> Optional[str]:
        """Wrapper to allow accuracy retries."""

        resp_history: list[str] = list()

        if not task_list:
            return None

        try:
            _iter_ = task_list.copy().__iter__()
            while action := next(_iter_, None):
                path_str: str | None = (
                    "Path: " + action.path
                    if hasattr(action, "path") and action.path.upper() not in ["N/A", "NONE", ""]
                    else None
                )
                task: str = f"{action.task}  {path_str or ''}"
                if agent_output := agent.invoke(task):
                    resp_history.append(agent_output)
                    shared.context.push("HISTORY", task)
                    shared.context.push("HISTORY", agent_output, "assistant")
                    task_list.pop(0)
        except (InterruptionRequest, TerminatingQuery) as err:
            return str(err)
        except self.RETRIABLE_ERRORS:
            events.reply.emit(reply=AIReply.error(msg.sorry_retry()))
            raise

        return os.linesep.join(resp_history) if resp_history else msg.no_output("Task-Splitter")


assert (splitter := TaskSplitter().INSTANCE) is not None
