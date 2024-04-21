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
import os
from typing import Optional, TypeAlias

from askai.core.askai_configs import configs
from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.features.actions import features
from askai.core.features.tools.analysis import assert_accuracy
from askai.core.features.tools.general import final_answer
from askai.core.model.action_plan import ActionPlan
from askai.core.support.langchain_support import lc_llm
from askai.core.support.object_mapper import object_mapper
from askai.core.support.shared_instances import shared
from askai.exception.exceptions import InaccurateResponse, MaxInteractionsReached
from hspylib.core.metaclass.singleton import Singleton
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables.utils import Input, Output
from retry import retry

RunnableTool: TypeAlias = Runnable[list[Input], list[Output]]


class Router(metaclass=Singleton):
    """Class to provide a divide and conquer set of actions to fulfill an objective. This is responsible for the
    orchestration and execution of the actions."""

    INSTANCE: "Router"

    REMINDER_MSG: str = "(Reminder to ALWAYS respond with a valid list of one or more tools.)"

    def __init__(self):
        self._approved = False

    @property
    def template(self) -> str:
        return prompt.read_prompt("router.txt")

    def process(self, query: str) -> Optional[str]:
        """Process the user query and retrieve the final response.
        :param query: The user query to complete.
        """

        @retry(exceptions=InaccurateResponse, tries=configs.max_router_retries, backoff=0)
        def _process_wrapper(question: str) -> Optional[str]:
            """Wrapper to allow RAG retries.
            :param question: The user query to complete.
            """
            template = PromptTemplate(input_variables=[
                "tools", "tool_names", "os_type", "user"
            ], template=self.template)
            final_prompt = template.format(
                tools=features.enlist(), tool_names=features.tool_names,
                os_type=prompt.os_type, user=prompt.user
            )
            log.info("Router::[QUESTION] '%s'", question)
            router_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", final_prompt),
                    MessagesPlaceholder("chat_history", optional=True),
                    ("human",  "{scratchpad}\n\n{input}\n" + self.REMINDER_MSG),
                ]
            )
            runnable = router_prompt | lc_llm.create_chat_model()
            chain = RunnableWithMessageHistory(
                runnable, shared.context.flat, input_messages_key="input", history_messages_key="chat_history"
            )
            response = chain.invoke({
                "input": query, "scratchpad": str(shared.context.flat("SCRATCHPAD"))
            }, config={"configurable": {"session_id": "HISTORY"}})
            if response:
                log.info("Router::[RESPONSE] Received from AI: \n%s.", str(response))
                plan: ActionPlan = object_mapper.of_json(response.content, ActionPlan)
                if not isinstance(plan, ActionPlan):
                    return str(plan)
                AskAiEvents.ASKAI_BUS.events.reply.emit(
                    message=msg.action_plan(f"[{plan.category.upper()}] {plan.reasoning}"),
                    verbosity="debug"
                )
                output = self._route(question, plan)
            else:
                output = response
            return output

        return _process_wrapper(query)

    def _route(self, query: str, plan: ActionPlan) -> str:
        """Route the actions to the proper function invocations.

        :param query: The user query to complete.
        """
        last_response: str = ""
        accumulated: list[str] = []
        actions: list[ActionPlan.Action] = plan.actions
        for idx, action in enumerate(actions):
            AskAiEvents.ASKAI_BUS.events.reply.emit(
                message=f"> `{action.tool}({', '.join(action.params)})`", verbosity="debug"
            )
            if idx >= configs.max_iteractions:
                AskAiEvents.ASKAI_BUS.events.reply_error.emit(message=msg.too_many_actions())
                raise MaxInteractionsReached(f"Maximum number of action was reached")
            if not (last_response := features.invoke(action, last_response)):
                log.warning("Last result brought an empty response for '%s'", action)
                break
            accumulated.append(f"AI Response: {last_response}")

        assert_accuracy(query, os.linesep.join(accumulated))
        shared.context.clear("SCRATCHPAD")

        return self._wrap_answer(query, plan.category, msg.translate(last_response))

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
