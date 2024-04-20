import logging as log
import os
from functools import lru_cache
from typing import Optional, TypeAlias

from hspylib.core.metaclass.singleton import Singleton
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables.utils import Input, Output
from retry import retry

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.features.actions import features
from askai.core.features.tools.analysis import assert_accuracy
from askai.core.model.action_plan import ActionPlan
from askai.core.support.langchain_support import lc_llm
from askai.core.support.object_mapper import object_mapper
from askai.core.support.shared_instances import shared
from askai.exception.exceptions import InaccurateResponse, MaxInteractionsReached

RunnableTool: TypeAlias = Runnable[list[Input], list[Output]]


class Router(metaclass=Singleton):
    """Class to provide a divide and conquer set of actions to fulfill an objective. This is responsible for the
    orchestration and execution of the actions."""

    INSTANCE: "Router" = None

    MAX_RETRIES: int = 5  # Move to configs

    MAX_REQUESTS: int = 30  # Move to config

    REMINDER_MSG: str = "(Reminder to ALWAYS respond with a valid list of one or more tools.)"

    def __init__(self):
        self._approved = False

    @lru_cache
    def template(self) -> str:
        return prompt.read_prompt("router.txt")

    def process(self, query: str) -> Optional[str]:
        """Process the user query and retrieve the final response.
        :param query: The user query to complete.
        """

        @retry(exceptions=InaccurateResponse, tries=Router.MAX_RETRIES, delay=0, backoff=0)
        def _process_wrapper(question: str) -> Optional[str]:
            """Wrapper to allow RAG retries.
            :param question: The user query to complete.
            """
            template = PromptTemplate(input_variables=["tools", "tool_names", "os_type"], template=self.template())
            final_prompt = template.format(
                tools=features.enlist(), tool_names=features.tool_names, os_type=prompt.os_type
            )
            log.info("Router::[QUESTION] '%s'", question)
            router_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", final_prompt),
                    MessagesPlaceholder("chat_history", optional=True),
                    ("human", self._scratch_pad() + "\n\n{input}\n" + self.REMINDER_MSG),
                ]
            )
            runnable = router_prompt | lc_llm.create_chat_model()
            chain = RunnableWithMessageHistory(
                runnable, shared.context.flat, input_messages_key="input", history_messages_key="chat_history"
            )
            if response := chain.invoke({"input": query}, config={"configurable": {"session_id": "HISTORY"}}):
                log.info("Router::[RESPONSE] Received from AI: \n%s.", str(response))
                action_plan: ActionPlan = object_mapper.of_json(response.content, ActionPlan)
                if not isinstance(action_plan, ActionPlan):
                    return str(action_plan)
                AskAiEvents.ASKAI_BUS.events.reply.emit(
                    message=msg.action_plan(action_plan.reasoning), verbosity="debug"
                )
                output = self._route(question, action_plan.actions)
            else:
                output = response
            return output

        return _process_wrapper(query)

    def _route(self, query: str, actions: list[ActionPlan.Action]) -> str:
        """Route the actions to the proper function invocations.

        :param query: The user query to complete.
        """
        last_response: str = ""
        accumulated: list[str] = []
        for idx, action in enumerate(actions):
            AskAiEvents.ASKAI_BUS.events.reply.emit(
                message=f"> `{action.tool}({', '.join(action.params)})`", verbosity="debug"
            )
            if idx > self.MAX_REQUESTS:
                AskAiEvents.ASKAI_BUS.events.reply_error.emit(message=msg.too_many_actions())
                raise MaxInteractionsReached(f"Maximum number of action was reached")
            if not (last_response := features.invoke(action, last_response)):
                log.warning("Last result brought an empty response for '%s'", action)
                break
            accumulated.append(f"AI Response: {last_response}")

        assert_accuracy(query, os.linesep.join(accumulated))

        return self._final_answer(query, last_response)

    def _scratch_pad(self) -> Optional[str]:
        """Return a scratchpad from the AI response failures."""
        return str(shared.context.flat("SCRATCHPAD"))

    def _final_answer(self, question: str, response: str) -> str:
        """Provide a final answer to the user.
        :param question: The user question.
        :param response: The AI response.
        """
        # TODO For now we are just using Taius, but we can opt to use Taius, STT, no persona, or custom.
        # return final_answer(question, response)
        return response


assert (router := Router().INSTANCE) is not None
