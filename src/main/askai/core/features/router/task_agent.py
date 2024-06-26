import logging as log
import os
from types import SimpleNamespace

from hspylib.core.metaclass.singleton import Singleton
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from askai.core.askai_configs import configs
from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperature import Temperature
from askai.core.enums.rag_response import RagResponse
from askai.core.enums.routing_model import RoutingModel
from askai.core.features.rag.rag import assert_accuracy
from askai.core.features.router.task_toolkit import features
from askai.core.features.router.tools.general import final_answer
from askai.core.model.action_plan import ActionPlan
from askai.core.model.model_result import ModelResult
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared


class TaskAgent(metaclass=Singleton):
    """This Langchain agent is responsible for executing the routers tasks using the available tools."""

    INSTANCE: "TaskAgent"

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
            model: RoutingModel = RoutingModel.of_model(model_result.mid)
            events.reply.emit(message=msg.model_select(str(model)), verbosity="debug")
            match model, configs.is_speak:
                case RoutingModel.TERMINAL_COMMAND, True:
                    output = final_answer(query, persona_prompt=f"taius-stt", response=response)
                case RoutingModel.ASSISTIVE_TECH_HELPER, _:
                    output = final_answer(query, persona_prompt=f"taius-stt", response=response)
                case RoutingModel.CHAT_MASTER, _:
                    output = final_answer(query, persona_prompt=f"taius-jarvis", response=response)
                case _:
                    # Default is to leave the AI response intact.
                    pass

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
        shared.context.push("HISTORY", query)
        output: str = ""
        events.reply.emit(message=plan.thoughts.speak)
        tasks: list[SimpleNamespace] = plan.tasks
        result_log: list[str] = []

        for idx, action in enumerate(tasks, start=1):
            path_str: str = 'Path: ' + action.path \
                if hasattr(action, 'path') and action.path.upper() not in ['N/A', 'NONE'] \
                else ''
            task = f"Task: {action.task}  {path_str}"
            events.reply.emit(message=msg.task(task), verbosity="debug")
            if (response := self.lc_agent.invoke({"input": task})) and (output := response["output"]):
                log.info("Router::[RESPONSE] Received from AI: \n%s.", output)
                assert_accuracy(task, output, RagResponse.MODERATE)
                shared.context.push("HISTORY", task, "assistant")
                shared.context.push("HISTORY", output, "assistant")
                shared.memory.save_context({"input": task}, {"output": output})
                result_log.append(output)
                if idx < len(tasks):  # Print intermediary steps.
                    events.reply.emit(message=output)
                continue

        assert_accuracy(query, os.linesep.join(result_log), RagResponse.GOOD)

        return self.wrap_answer(plan.primary_goal, output, plan.model)

    def _create_lc_agent(self, temperature: Temperature = Temperature.CODE_GENERATION) -> Runnable:
        """Create the LangChain agent.
        :param temperature: The LLM temperature (randomness).
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


assert (agent := TaskAgent().INSTANCE) is not None
