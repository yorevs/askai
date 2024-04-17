import logging as log
import os
import re
from functools import lru_cache
from typing import TypeAlias, Optional

from hspylib.core.metaclass.singleton import Singleton
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables.utils import Input, Output
from retry import retry

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.features.actions import features
from askai.core.features.tools.analysis import assert_accuracy
from askai.core.features.tools.general import final_answer
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.exception.exceptions import InaccurateResponse, MaxInteractionsReached

RunnableTool: TypeAlias = Runnable[list[Input], list[Output]]


class Router(metaclass=Singleton):
    """Class to provide a divide and conquer set of actions to fulfill an objective. This is responsible for the
    orchestration and execution of the actions."""

    INSTANCE: 'Router' = None

    MAX_RETRIES: int = 5    # Move to configs

    MAX_REQUESTS: int = 30  # Move to config

    def __init__(self):
        self._approved = False

    @lru_cache
    def template(self) -> str:
        return prompt.read_prompt("router-prompt.txt")

    def process(self, query: str) -> Optional[str]:
        """Process the user query and retrieve the final response."""
        @retry(exceptions=InaccurateResponse, tries=Router.MAX_RETRIES, delay=0, backoff=0)
        def _process_wrapper(question: str) -> Optional[str]:
            """Wrapper to allow RAG retries."""
            template = PromptTemplate(input_variables=[
                'tools', 'tool_names', 'os_type'
            ], template=self.template())
            final_prompt = template.format(
                tools=features.enlist(), tool_names=features.tool_names,
                os_type=prompt.os_type)
            log.info("Router::[QUESTION] '%s'", question)
            chat_prompt = ChatPromptTemplate.from_messages([
                ("system", final_prompt),
                MessagesPlaceholder("chat_history", optional=True),
                ("human", "{input}\n\n (Reminder to ALWAYS respond with a valid list of one or more tools.)'")])
            runnable = chat_prompt | lc_llm.create_chat_model()
            chain = RunnableWithMessageHistory(
                runnable, shared.context.flat,
                input_messages_key="input", history_messages_key="chat_history",
            )
            if response := chain.invoke({"input": query}, config={"configurable": {"session_id": "HISTORY"}}):
                log.info("Router::[RESPONSE] Received from AI: \n%s.", str(response))
                actions: list[str] = re.sub(r'\d+[.:)-]\s+', '', response.content).split(os.linesep)
                actions = list(filter(len, map(str.strip, actions)))
                AskAiEvents.ASKAI_BUS.events.reply.emit(
                    message=msg.action_plan('` -> `'.join(actions)), verbosity='debug')
                output = self._route(question, actions)
            else:
                output = response
            return output

        return _process_wrapper(query)

    def _route(self, question: str, actions: list[str]) -> str:
        """Route the actions to the proper function invocations."""
        max_iteraction: int = self.MAX_REQUESTS
        last_result: str = ''
        accumulated: list[str] = []
        for idx, action in enumerate(actions):
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=f"> `{action}`", verbosity='debug')
            if idx > max_iteraction:
                AskAiEvents.ASKAI_BUS.events.reply_error.emit(message=msg.too_many_actions())
                raise MaxInteractionsReached(f"Maximum number of action was reached")
            if not (last_result := features.invoke(action, last_result)):
                log.warning("Last result brought an empty response for '%s'", action)
                break
            accumulated.append(f"AI Response: {last_result}")

        assert_accuracy(question, os.linesep.join(accumulated))

        return self._final_answer(question, last_result)

    def _final_answer(self, question: str, response: str) -> str:
        """Provide a final answer to the user."""
        # TODO For now we are just using Taius, but we can opt to use Taius, STT, no persona, or custom.
        return final_answer(question, response)


assert (router := Router().INSTANCE) is not None
