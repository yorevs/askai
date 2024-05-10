#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.features.tools.analysis
      @file: analysis.py
   @created: Mon, 01 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

import logging as log

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperature import Temperature
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import ensure_ln


def query_output(query: str, context: str = None) -> str:
    """Handle 'Text analysis', invoking: analyze(question: str). Analyze the context and answer the question.
    :param query: The question about the content to be analyzed.
    :param context: The context of the question.
    """
    output = None
    template = ChatPromptTemplate.from_messages(
        [
            ("system", prompt.read_prompt("analysis")),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
        ]
    )
    if context or (context := str(shared.context.flat("HISTORY"))):
        runnable = template | lc_llm.create_chat_model(Temperature.DATA_ANALYSIS.temp)
        runnable = RunnableWithMessageHistory(
            runnable,
            shared.context.flat,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
        log.info("Analysis::[QUERY] '%s'  context=%s", query, context)
        if response := runnable.invoke({"input": query}, config={"configurable": {"session_id": "HISTORY"}}):
            output = response.content
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.analysis(output), verbosity="debug")

    return ensure_ln(output or msg.translate("Sorry, I don't know."))
