import logging as log
from types import SimpleNamespace

from hspylib.core.metaclass.singleton import Singleton
from langchain.agents import AgentExecutor, create_structured_chat_agent
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
from askai.core.model.model_result import ModelResult
from askai.core.model.rag_response import RagResponse
from askai.core.model.routing_model import RoutingModel
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.exception.exceptions import InaccurateResponse


class RouterAgent(metaclass=Singleton):
    """This Langchain agent is responsible for executing the routers tasks using the available tools."""

    INSTANCE: "RouterAgent"

    @staticmethod
    def wrap_answer(
        query: str,
        response: str,
        model_result: ModelResult = ModelResult.default()
    ) -> str:
        """Provide a final answer to the user.
        :param query: The user question.
        :param response: The AI response.
        :param model_result: The selected routing model.
        """
        output: str = msg.translate(response)
        if model_result:
            model: RoutingModel = RoutingModel.value_of(model_result.mid)
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.model_select(str(model)), verbosity="debug")
            match model, configs.is_speak:
                case RoutingModel.ASK_001, True:  # TERMINAL_COMMAND
                    output = final_answer(query, persona_prompt="stt", response=response)
                case RoutingModel.ASK_008, _:  # ASSISTIVE_TECH_HELPER
                    output = final_answer(query, persona_prompt="stt", response=response)
                case RoutingModel.ASK_007 | RoutingModel.ASK_005, _:  # IMAGE_PROCESSOR | CHAT_MASTER
                    output = final_answer(query, response=response)

        cache.save_reply(query, output)

        return output

    def __init__(self):
        self._lc_agent: Runnable | None = None

    @property
    def agent_template(self) -> ChatPromptTemplate:
        """Retrieve the Structured Agent Template."""
        return prompt.hub("hwchase17/structured-chat-agent")

    @property
    def lc_agent(self) -> Runnable:
        return self._create_lc_agent()

    def invoke(self, query: str, plan: ActionPlan) -> str:
        """Invoke the agent to respond the given query, using the specified action plan.
        :param query: The user question.
        :param plan: The AI action plan.
        """
        output: str = ""
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=plan.thoughts.speak)
        tasks: list[SimpleNamespace] = plan.tasks

        for action in tasks:
            path_str: str = 'Path: ' + action.path \
                if hasattr(action, 'path') and action.path.upper() not in ['N/A', 'NONE'] \
                else ''
            task = f"Task: {action.task}  {path_str}"
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=f"> {task}", verbosity="debug")
            if (response := self.lc_agent.invoke({"input": task})) and (output := response["output"]):
                log.info("Router::[RESPONSE] Received from AI: \n%s.", output)
                assert_accuracy(task, output, RagResponse.MODERATE)
                shared.context.push("HISTORY", task)
                shared.context.push("HISTORY", output, "assistant")
                shared.memory.save_context({"input": task}, {"output": output})
                continue
            raise InaccurateResponse("AI provided AN EMPTY response")

        assert_accuracy(query, output, RagResponse.GOOD)

        return self.wrap_answer(plan.primary_goal, output, plan.model)

    def _create_lc_agent(self, temperature: Temperature = Temperature.CODE_GENERATION) -> Runnable:
        """Create the LangChain agent.
        :param temperature: The LLM temperature.
        """
        if self._lc_agent is None:
            tools = features.tools()
            llm = lc_llm.create_chat_model(temperature.temp)
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


assert (agent := RouterAgent().INSTANCE) is not None
