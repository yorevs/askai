#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.features.rag.commons
      @file: analysis.py
   @created: Fri, 03 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

import logging as log

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.geo_location import geo_location
from askai.core.engine.openai.temperature import Temperature
from askai.core.model.rag_response import RagResponse
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.exception.exceptions import InaccurateResponse


def assert_accuracy(question: str, ai_response: str, pass_threshold: RagResponse = RagResponse.MODERATE) -> None:
    """Function responsible for asserting that the question was properly answered.
    :param question: The user question.
    :param ai_response: The AI response to be analysed.
    :param pass_threshold: The threshold color to be considered as a pass.
    """
    issues_prompt = PromptTemplate(input_variables=["problems"], template=prompt.read_prompt("assert"))
    if ai_response in msg.accurate_responses:
        return
    elif not ai_response:
        empty_msg = "AI provided a BAD response (empty)"
        details = issues_prompt.format(problems=empty_msg)
        shared.context.push("RAG", issues_prompt.format(problems=empty_msg))
        raise InaccurateResponse(details)

    assert_template = PromptTemplate(input_variables=["datetime", "input", "response"], template=prompt.read_prompt("rag"))
    final_prompt = assert_template.format(datetime=geo_location.datetime, input=question, response=ai_response)
    log.info("Assert::[QUESTION] '%s'  context: '%s'", question, ai_response)
    llm = lc_llm.create_chat_model(Temperature.DATA_ANALYSIS.temp)
    response: AIMessage = llm.invoke(final_prompt)

    if response and (output := response.content):
        if mat := RagResponse.matches(output):
            status, details = mat.group(1), mat.group(2)
            log.info("Accuracy check ->  status: '%s'  reason: '%s'", status, details)
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.assert_acc(output), verbosity="debug")
            if not RagResponse.of_status(status).passed(pass_threshold):
                shared.context.push("RAG", issues_prompt.format(problems=RagResponse.strip_code(output)))
                raise InaccurateResponse(f"AI Assistant failed to respond => '{response.content}'")
            return

    raise InaccurateResponse(f"AI Assistant didn't respond accurately => '{response.content}'")


def resolve_x_refs(ref_name: str, context: str | None = None) -> str:
    """Replace all cross references by their actual values.
    :param ref_name: The cross-reference or variable name.
    :param context: The context to analyze the references.
    """
    template = ChatPromptTemplate.from_messages(
        [
            ("system", prompt.read_prompt("x-references")),
            MessagesPlaceholder("context", optional=True),
            ("human", "{pathname}"),
        ]
    )
    output = ref_name
    if context or (context := str(shared.context.flat("HISTORY"))):
        runnable = template | lc_llm.create_chat_model(Temperature.DATA_ANALYSIS.temp)
        runnable = RunnableWithMessageHistory(
            runnable, shared.context.flat, input_messages_key="pathname", history_messages_key="context"
        )
        log.info("Analysis::[QUERY] '%s'  context=%s", ref_name, context)
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.x_reference(ref_name), verbosity="debug")
        response = runnable.invoke({"pathname": ref_name}, config={"configurable": {"session_id": "HISTORY"}})
        if response and (output := response.content) and shared.UNCERTAIN_ID != output:
            output = response.content

    return output
