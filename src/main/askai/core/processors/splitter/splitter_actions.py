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
import logging as log
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

from hspylib.core.metaclass.singleton import Singleton
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory

from askai.core.askai_configs import configs
from askai.core.askai_prompt import prompt
from askai.core.component.geo_location import geo_location
from askai.core.component.rag_provider import RAGProvider
from askai.core.engine.openai.temperature import Temperature
from askai.core.enums.response_model import ResponseModel
from askai.core.model.acc_response import AccResponse
from askai.core.model.action_plan import ActionPlan
from askai.core.model.model_result import ModelResult
from askai.core.router.agent_tools import features
from askai.core.router.task_agent import agent
from askai.core.router.tools.general import final_answer
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared


class SplitterActions(metaclass=Singleton):
    """TODO"""

    INSTANCE: 'SplitterActions'

    @staticmethod
    def wrap_answer(question: str, answer: str, model_result: ModelResult = ModelResult.default()) -> str:
        """Provide a final answer to the user by wrapping the AI response with additional context.
        :param question: The user's question.
        :param answer: The AI's response to the question.
        :param model_result: The result from the selected routing model (default is ModelResult.default()).
        :return: A formatted string containing the final answer.
        """
        output: str = answer
        args = {"user": prompt.user.title(), "idiom": shared.idiom, "context": answer, "question": question}
        prompt_args: list[str] = [k for k in args.keys()]
        model: ResponseModel = ResponseModel.of_model(model_result.mid)
        # events.reply.emit(reply=AIReply.full(msg.model_select(model)))

        match model, configs.is_speak:
            case ResponseModel.TERMINAL_COMMAND, True:
                output = final_answer("taius-stt", prompt_args, **args)
            case ResponseModel.ASSISTIVE_TECH_HELPER, _:
                output = final_answer("taius-stt", prompt_args, **args)
            case ResponseModel.CHAT_MASTER, _:
                output = final_answer("taius-jarvis", prompt_args, **args)
            case _:
                pass  # Default is to leave the last AI response as is

        # Save the conversation to use with the task agent executor.
        shared.memory.save_context({"input": question}, {"output": output})

        return output

    @staticmethod
    def refine_answer(question: str, answer: str, acc_response: AccResponse | None = None) -> str:
        """TODO
        :param question: The user's question.
        :param answer: The AI's response to the question.
        :param acc_response: The final accuracy response, if available.
        """
        if acc_response and acc_response.reasoning:
            ctx: str = str(shared.context.flat("HISTORY"))
            args = {
                "improvements": acc_response.details,
                "context": ctx,
                "response": answer,
                "question": question,
            }
            prompt_args = [k for k in args.keys()]
            # events.reply.emit(reply=AIReply.debug(msg.refine_answer(answer)))
            return final_answer("taius-refiner", prompt_args, **args)

        return answer

    @staticmethod
    def process_action(action: SimpleNamespace) -> str:
        """TODO"""
        path_str: str | None = (
            "Path: " + action.path
            if hasattr(action, "path") and action.path.upper() not in ["N/A", "NONE", ""]
            else None
        )
        task: str = f"{action.task}  {path_str or ''}"
        return agent.invoke(task)

    def __init__(self):
        self._rag: RAGProvider = RAGProvider("task-splitter.csv")

    def splitter_template(self, query: str) -> ChatPromptTemplate:
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
                ("human", "Human Question: '{input}'"),
            ]
        )

    def split(self, question: str, model: ModelResult = ModelResult.default()) -> Optional[ActionPlan]:
        """Invoke the LLM to split the tasks and create an action plan."""
        runnable = self.splitter_template(question) | lc_llm.create_chat_model(Temperature.COLDEST.temp)
        runnable = RunnableWithMessageHistory(
            runnable, shared.context.flat, input_messages_key="input", history_messages_key="chat_history"
        )
        response: AIMessage
        if response := runnable.invoke({"input": question}, config={"configurable": {"session_id": "HISTORY"}}):
            answer: str = str(response.content)
            log.info("Router::[RESPONSE] Received from AI: \n%s.", answer)
            return ActionPlan.create(question, answer, model)

        return None


assert (actions := SplitterActions().INSTANCE) is not None
