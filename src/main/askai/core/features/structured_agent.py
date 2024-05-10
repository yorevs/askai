import logging as log
from types import SimpleNamespace

from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_argument
from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from askai.core.askai_configs import configs
from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import cache
from askai.core.engine.openai.temperature import Temperature
from askai.core.features.actions import features
from askai.core.features.rag.rag import assert_accuracy, final_answer
from askai.core.model.action_plan import ActionPlan
from askai.core.model.category import Category
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.exception.exceptions import InaccurateResponse


class StructuredAgent(metaclass=Singleton):
    """TODO"""

    INSTANCE: 'StructuredAgent'

    @staticmethod
    def _wrap_answer(query: str, category_str: str, response: str) -> str:
        """Provide a final answer to the user.
        :param query: The user question.
        :param category_str: The category of the question.
        :param response: The AI response.
        """
        output: str = response
        category: Category = Category.of_value(category_str)
        match category, configs.is_speak:
            case Category.FILE_MANAGEMENT | Category.TERMINAL_COMMAND, True:
                output = final_answer(query, persona_prompt="stt", response=response)
            case Category.ASSISTIVE_REQUESTS, _:
                output = final_answer(query, persona_prompt="stt", response=response)
            case Category.IMAGE_CAPTION | Category.CONVERSATIONAL, _:
                output = final_answer(query, response=response)

        cache.save_reply(query, output)

        return output

    @staticmethod
    def _assert_actions(actions, *attrs):
        """TODO"""
        check_argument(
            actions is not None and len(actions) > 0,
            "Invalid Actions (None or Empty)")
        check_argument(
            all(isinstance(act, SimpleNamespace) for act in actions),
            "Invalid action format (JSON)")
        check_argument(
            all(hasattr(act, attr) for attr in attrs for act in actions),
            "Invalid action arguments")

    def __init__(self):
        self._lc_agent: Runnable | None = None

    @property
    def agent_template(self) -> ChatPromptTemplate:
        """Retrieve the Structured Agent Template."""
        return prompt.hub("hwchase17/structured-chat-agent")

    @property
    def lc_agent(self) -> Runnable:
        """TODO"""
        return self._create_lc_agent()

    def invoke(self, query: str, action_plan: ActionPlan) -> str:
        """TODO"""
        output: str = ""
        actions: list[SimpleNamespace] = action_plan.actions
        self._assert_actions(actions, 'task', 'category')
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=action_plan.thoughts.speak)
        for action in actions:
            task = (
                f"Task: {action.task}  "
                f"{'Path: ' + action.path if hasattr(action, 'path') and action.path.upper() not in ['N/A', 'NONE'] else ''}"
            )
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=f"> {task}", verbosity="debug")
            if (response := self.lc_agent.invoke({"input": task})) and (output := response["output"]):
                log.info("Router::[RESPONSE] Received from AI: \n%s.", output)
                assert_accuracy(task, output)
                shared.context.push("HISTORY", task)
                shared.context.push("HISTORY", output, "assistant")
                shared.memory.save_context({'input': task}, {'output': output})
                continue
            raise InaccurateResponse("AI provided AN EMPTY response")

        return self._wrap_answer(query, action_plan.category, msg.translate(output))

    def _create_lc_agent(self) -> Runnable:
        """TODO"""
        if self._lc_agent is None:
            tools = features.agent_tools()
            llm = lc_llm.create_chat_model(Temperature.COLDEST.temp)
            chat_memory = shared.memory
            lc_agent = create_structured_chat_agent(llm, tools, self.agent_template)
            self._lc_agent = AgentExecutor(
                agent=lc_agent,
                tools=tools,
                max_iteraction=configs.max_router_retries,
                memory=chat_memory,
                handle_parsing_errors=True,
                max_execution_time=configs.max_agent_execution_time_seconds,
                verbose=configs.is_debug,
            )

        return self._lc_agent


assert (agent := StructuredAgent().INSTANCE) is not None
