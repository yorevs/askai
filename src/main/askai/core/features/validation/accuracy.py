#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.features.rag.commons
      @file: analysis.py
   @created: Fri, 03 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.geo_location import geo_location
from askai.core.engine.openai.temperature import Temperature
from askai.core.enums.acc_response import AccResponse
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.exception.exceptions import InaccurateResponse
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from textwrap import dedent

import logging as log

EVALUATION_GUIDE: str = dedent(
    """
**Accuracy Evaluation Guidelines:**

1. Review and analyze your past responses to ensure optimal accuracy.
2. Constructively self-criticize your overall responses regularly.
3. Reflect on past decisions and strategies to refine your approach.
4. Try something different.
"""
).strip()


def assert_accuracy(
    question: str,
    ai_response: str,
    pass_threshold: AccResponse = AccResponse.MODERATE
) -> AccResponse:
    """Function responsible for asserting that the question was properly answered.
    :param question: The user question.
    :param ai_response: The AI response to be analysed.
    :param pass_threshold: The threshold color to be considered as a pass.
    """
    if ai_response and ai_response not in msg.accurate_responses:
        issues_prompt = PromptTemplate(
            input_variables=["problems"], template=prompt.read_prompt("assert")
        )
        assert_template = PromptTemplate(
            input_variables=["datetime", "input", "response"], template=prompt.read_prompt("accuracy")
        )
        final_prompt = assert_template.format(datetime=geo_location.datetime, input=question, response=ai_response)
        log.info("Assert::[QUESTION] '%s'  context: '%s'", question, ai_response)
        llm = lc_llm.create_chat_model(Temperature.COLDEST.temp)
        response: AIMessage = llm.invoke(final_prompt)

        if response and (output := response.content):
            if mat := AccResponse.matches(output):
                status, details = mat.group(1), mat.group(2)
                log.info("Accuracy check ->  status: '%s'  reason: '%s'", status, details)
                events.reply.emit(message=msg.assert_acc(status, details), verbosity="debug")
                if not (rag_resp := AccResponse.of_status(status, details)).passed(pass_threshold):
                    # Include the guidelines for the first mistake.
                    if not shared.context.get("EVALUATION"):
                        shared.context.push("EVALUATION", EVALUATION_GUIDE)
                    shared.context.push("EVALUATION", issues_prompt.format(problems=AccResponse.strip_code(output)))
                    raise InaccurateResponse(f"AI Assistant failed to respond => '{response.content}'")
                return rag_resp
        # At this point, the response was not Good.
        raise InaccurateResponse(f"AI Assistant didn't respond accurately. Response: '{response}'")

    events.reply.emit(message=msg.no_output("query"))


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
        runnable = template | lc_llm.create_chat_model(Temperature.CODE_GENERATION.temp)
        runnable = RunnableWithMessageHistory(
            runnable, shared.context.flat, input_messages_key="pathname", history_messages_key="context"
        )
        log.info("Analysis::[QUERY] '%s'  context=%s", ref_name, context)
        events.reply.emit(message=msg.x_reference(ref_name), verbosity="debug")
        response = runnable.invoke({"pathname": ref_name}, config={"configurable": {"session_id": "HISTORY"}})
        if response and (output := response.content) and shared.UNCERTAIN_ID != output:
            output = response.content

    return output
