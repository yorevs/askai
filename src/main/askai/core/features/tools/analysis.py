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

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperature import Temperature
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter
from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate


def query_output(question: str, context: str | None = None) -> str:
    """Handle 'Text analysis', invoking: analyze(question: str). Analyze the context and answer the question.
    :param question: The question about the content to be analyzed.
    :param context: The context of the question.
    """
    output = None
    if context or (context := str(shared.context.flat("HISTORY"))):
        log.info("Analysis::[QUESTION] '%s'  context=%s", question, context)
        llm = lc_llm.create_chat_model(Temperature.DATA_ANALYSIS.temp)
        template = PromptTemplate(input_variables=["context", "question"], template=prompt.read_prompt("analysis"))
        final_prompt = template.format(context=context, question=question)
        response: AIMessage = llm.invoke(final_prompt)
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.analysis(response.content), verbosity="debug")

        if response and (output := response.content):
            shared.context.push("HISTORY", question)
            shared.context.push("HISTORY", output, "assistant")
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=output, verbosity="debug")
            output = text_formatter.ensure_ln(output)

    return output or msg.translate("Sorry, I don't know.")
