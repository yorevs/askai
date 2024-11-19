#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.router.task_agent
      @file: task_agent.py
   @created: Tue, 24 Jun 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.askai_configs import configs
from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperature import Temperature
from askai.core.model.ai_reply import AIReply
from askai.core.router.agent_tools import features
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from hspylib.core.config.path_object import PathObject
from hspylib.core.metaclass.singleton import Singleton
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.memory.chat_memory import BaseChatMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain_core.runnables.utils import Output
from typing import AnyStr, Optional

import logging as log
import openai


class TaskAgent(metaclass=Singleton):
    """A LangChain agent responsible for executing router tasks using the available tools. This agent manages and
    performs tasks by leveraging various tools, ensuring efficient and accurate task execution in the routing process.
    """

    INSTANCE: "TaskAgent"

    @property
    def agent_template(self) -> ChatPromptTemplate:
        """Retrieve the Structured Agent Template for use in the chat agent. This template is used to structure the
        interactions of the chat agent.
        Reference: https://smith.langchain.com/hub/hwchase17/structured-chat-agent
        :return: An instance of ChatPromptTemplate representing the structured agent template.
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

    def invoke(self, task: str) -> Optional[str]:
        """Invoke the agent to respond to the given query using the specified action plan.
        :param task: The AI task that outlines the steps to generate the response.
        :return: The agent's response as a string.
        """
        output: str | None = None
        events.reply.emit(reply=AIReply.debug(msg.task(task)))
        shared.context.push("HISTORY", task, "assistant")
        if (response := self._exec_task(task)) and (output := response["output"]):
            log.info("Router::[RESPONSE] Received from AI: \n%s.", output)
            shared.context.push("HISTORY", output, "assistant")

        return output

    def _create_lc_agent(self, temperature: Temperature = Temperature.COLDEST) -> Runnable:
        """Create and return a LangChain agent.
        :param temperature: The LLM temperature, which controls the randomness of the responses (default is
                            Temperature.COLDEST).
        :return: An instance of a Runnable representing the LangChain agent.
        """

        tools = features.tools()
        llm = lc_llm.create_chat_model(temperature.temp)
        chat_memory: BaseChatMemory = shared.memory
        lc_agent = create_structured_chat_agent(llm, tools, self.agent_template)
        lc_agent: Runnable = AgentExecutor(
            agent=lc_agent,
            tools=tools,
            max_iterations=configs.max_agent_retries,
            memory=chat_memory,
            handle_parsing_errors="Generate a JSON blob that is fully parseable using the Python `json` module.",
            max_execution_time=configs.max_agent_execution_time_seconds,
            verbose=configs.is_debug,
        )

        return lc_agent

    def _exec_task(self, task: AnyStr) -> Optional[Output]:
        """Execute the specified agent task.
        :param task: The task to be executed by the agent.
        :return: An instance of Output containing the result of the task, or None if the task fails or produces
        no output.
        """
        try:
            lc_agent: Runnable = self._create_lc_agent()
            return lc_agent.invoke({"input": task})
        except openai.APIError as err:
            log.error(str(err))
        except ValueError as err:
            log.error(str(err))

        return None


assert (agent := TaskAgent().INSTANCE) is not None
