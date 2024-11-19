#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.processors.splitter.splitter_actions
      @file: splitter_actions.py
   @created: Mon, 21 Oct 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from pathlib import Path
from types import SimpleNamespace
from typing import Optional
import logging as log

from hspylib.core.metaclass.singleton import Singleton
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory, Runnable

from askai.core.askai_configs import configs
from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import cache
from askai.core.component.geo_location import geo_location
from askai.core.component.rag_provider import RAGProvider
from askai.core.engine.openai.temperature import Temperature
from askai.core.enums.response_model import ResponseModel
from askai.core.model.acc_response import AccResponse
from askai.core.model.action_plan import ActionPlan
from askai.core.model.ai_reply import AIReply
from askai.core.model.model_result import ModelResult
from askai.core.router.task_agent import agent
from askai.core.router.tools.general import final_answer
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter


class SplitterActions(metaclass=Singleton):
    """Class that provides the splitter some actionable items."""

    INSTANCE: "SplitterActions"

    @staticmethod
    def wrap_answer(question: str, answer: str, model_result: ModelResult = ModelResult.default()) -> Optional[str]:
        """Provide a final answer to the user by wrapping the AI response with additional context.
        :param question: The user's question.
        :param answer: The AI's response to the question.
        :param model_result: The result from the selected routing model (default is ModelResult.default()).
        :return: An optional formatted string containing the wrapped answer.
        """
        output: str = answer
        ctx: str = text_formatter.strip_format(answer)
        args = {"user": prompt.user.title(), "idiom": shared.idiom, "context": ctx, "question": question}
        prompt_args: list[str] = [k for k in args.keys()]
        model: ResponseModel = ResponseModel.of_model(model_result.mid)
        events.reply.emit(reply=AIReply.full(msg.model_select(model)))

        match model, configs.is_speak:
            case ResponseModel.TERMINAL_COMMAND, True:
                output = final_answer("taius-tts", prompt_args, **args)
            case ResponseModel.ASSISTIVE_TECH_HELPER, _:
                output = final_answer("taius-tts", prompt_args, **args)
            case ResponseModel.CHAT_MASTER, _:
                output = final_answer("taius-jarvis", prompt_args, **args)
            case _:
                pass  # Default is to leave the last AI response as is

        # Save the conversation to use with the task agent executor.
        cache.save_memory(shared.memory.buffer_as_messages)
        shared.context.save()

        return output

    @staticmethod
    def refine_answer(question: str, answer: str, acc_response: AccResponse | None = None) -> str:
        """Refine the AI response when required.
        :param question: The user's question.
        :param answer: The AI's response to the question.
        :param acc_response: The final accuracy response, if available.
        """
        if acc_response and acc_response.reasoning:
            ctx: str = text_formatter.strip_format(str(shared.context.flat("HISTORY")))
            args = {
                "locale": configs.language.locale,
                "user": prompt.user.title(),
                "improvements": acc_response.details,
                "context": ctx,
                "response": answer,
                "question": question,
            }
            prompt_args = [k for k in args.keys()]
            events.reply.emit(reply=AIReply.debug(msg.refine_answer(answer)))
            return final_answer("taius-refiner", prompt_args, **args)

        return answer

    @staticmethod
    def process_action(action: SimpleNamespace) -> Optional[str]:
        """Execute an action requested by the AI.
        :param action: Action to be executed, encapsulated in a SimpleNamespace.
        :return: Output resulted from the action execution as a string, or None if no output.
        """
        path_str: str | None = (
            "Path: " + action.path
            if hasattr(action, "path") and action.path.upper() not in ["N/A", "NONE", ""]
            else None
        )
        return agent.invoke(f"{action.task}  {path_str or ''}")

    def __init__(self):
        self._rag: RAGProvider = RAGProvider("task-splitter.csv")

    def splitter_template(self, query: str) -> ChatPromptTemplate:
        """Retrieve the processor template based on the given query.
        :param query: The input query to process and retrieve the template for.
        :return: A ChatPromptTemplate object that matches the query.
        """

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
                ("human", "Human Question: '{input}'"),
            ]
        )

    def split(self, question: str, model: ModelResult = ModelResult.default()) -> Optional[ActionPlan]:
        """Invoke the LLM to split the tasks and create an action plan.
        :param question: The input question to be processed.
        :param model: The model used to generate the action plan, defaulting to ModelResult.default().
        :return: An optional ActionPlan generated from the provided question.
        """

        response: AIMessage
        runnable: Runnable = self.splitter_template(question) | lc_llm.create_chat_model(Temperature.COLDEST.temp)
        runnable: Runnable = RunnableWithMessageHistory(
            runnable, shared.context.flat, input_messages_key="input", history_messages_key="chat_history"
        )
        if response := runnable.invoke({"input": question}, config={"configurable": {"session_id": "HISTORY"}}):
            answer: str = str(response.content)
            log.info("Router::[RESPONSE] Received from AI: \n%s.", answer)
            return ActionPlan.create(question, answer, model)

        return None


assert (actions := SplitterActions().INSTANCE) is not None
