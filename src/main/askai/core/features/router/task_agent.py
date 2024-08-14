import logging as log
import os
from typing import Optional

from hspylib.core.config.path_object import PathObject
from hspylib.core.metaclass.singleton import Singleton
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain_core.runnables.utils import Output

from askai.core.askai_configs import configs
from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperature import Temperature
from askai.core.enums.acc_response import AccResponse
from askai.core.enums.routing_model import RoutingModel
from askai.core.features.router.task_toolkit import features
from askai.core.features.router.tools.general import final_answer
from askai.core.features.validation.accuracy import assert_accuracy
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
        answer: str,
        model_result: ModelResult = ModelResult.default(),
        rag: AccResponse | None = None
    ) -> str:
        """Provide a final answer to the user.
        :param query: The user question.
        :param answer: The AI response.
        :param model_result: The selected routing model.
        :param rag: The final accuracy check (RAG) response.
        """
        output: str = answer
        model: RoutingModel = RoutingModel.of_model(model_result.mid)
        events.reply.emit(message=msg.model_select(str(model)), verbosity="debug")
        args = {'user': shared.username, 'idiom': shared.idiom, 'context': answer, 'question': query}

        match model, configs.is_speak:
            case RoutingModel.TERMINAL_COMMAND, True:
                output = final_answer("taius-stt", [k for k in args.keys()], **args)
            case RoutingModel.ASSISTIVE_TECH_HELPER, _:
                output = final_answer("taius-stt", [k for k in args.keys()], **args)
            case RoutingModel.CHAT_MASTER, _:
                output = final_answer("taius-jarvis", [k for k in args.keys()], **args)
            case RoutingModel.REFINER, _:
                if rag:
                    ctx: str = str(shared.context.flat("HISTORY"))
                    args = {'improvements': rag.reasoning, 'context': ctx, 'response': answer, 'question': query}
                    output = final_answer("taius-refiner", [k for k in args.keys()], **args)
            case _:
                # Default is to leave the last AI response intact.
                pass

        shared.context.push("HISTORY", query)
        shared.context.push("HISTORY", output, "assistant")
        shared.memory.save_context({"input": query}, {"output": output})

        return output

    def __init__(self):
        self._lc_agent: Runnable | None = None

    @property
    def agent_template(self) -> ChatPromptTemplate:
        """Retrieve the Structured Agent Template.
        Ref: https://smith.langchain.com/hub/hwchase17/structured-chat-agent
        """
        prompt_file: PathObject = PathObject.of(prompt.append_path(f"langchain/structured-chat-agent"))
        final_prompt: str = prompt.read_prompt(prompt_file.filename, prompt_file.abs_dir)
        return ChatPromptTemplate.from_messages(
            [
                ("system", final_prompt),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("user", "{input}"),
                ("assistant", "{agent_scratchpad}"),
            ]
        )

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
        accumulated: list[str] = []
        if tasks := plan.tasks:
            if plan.speak:
                events.reply.emit(message=plan.speak)
            for idx, action in enumerate(tasks, start=1):
                path_str: str = 'Path: ' + action.path \
                    if hasattr(action, 'path') and action.path.upper() not in ['N/A', 'NONE'] \
                    else ''
                task: str = f"{action.task}  {path_str}"
                events.reply.emit(message=msg.task(task), verbosity="debug")
                if (response := self._exec_action(task)) and (output := response["output"]):
                    log.info("Router::[RESPONSE] Received from AI: \n%s.", output)
                    if len(tasks) > 1:
                        assert_accuracy(task, output, AccResponse.MODERATE)
                        # Push intermediary steps to the chat history.
                        shared.context.push("HISTORY", task, "assistant")
                        shared.context.push("HISTORY", output, "assistant")
                        shared.memory.save_context({"input": task}, {"output": output})
                        if len(tasks) > idx:
                            # Print intermediary steps.
                            events.reply.emit(message=output)
                    accumulated.append(output)
                else:
                    output = msg.no_output("AI")
                    accumulated.append(output)
        else:
            output = plan.speak
            accumulated.append(output)

        if (rag := assert_accuracy(query, os.linesep.join(accumulated), AccResponse.MODERATE)).is_moderate:
            plan.model.mid = RoutingModel.REFINER.model

        return self.wrap_answer(plan.primary_goal, output, plan.model, rag)

    def _create_lc_agent(self, temperature: Temperature = Temperature.CODE_GENERATION) -> Runnable:
        """Create the LangChain agent.
        :param temperature: The LLM temperature (randomness).
        """
        if self._lc_agent is None:
            tools = features.tools()
            llm = lc_llm.create_chat_model(temperature.temp)
            chat_memory = shared.memory
            lc_agent = create_structured_chat_agent(llm, tools, self.agent_template)
            self._lc_agent: Runnable = AgentExecutor(
                agent=lc_agent,
                tools=tools,
                max_iteraction=configs.max_router_retries,
                memory=chat_memory,
                handle_parsing_errors=True,
                max_execution_time=configs.max_agent_execution_time_seconds,
                verbose=configs.is_debug,
            )

        return self._lc_agent

    def _exec_action(self, action: str) -> Optional[Output]:
        return self.lc_agent.invoke({"input": action})


assert (agent := TaskAgent().INSTANCE) is not None
