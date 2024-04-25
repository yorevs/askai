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

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperature import Temperature
from askai.core.model.rag_response import RagResponse
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter
from askai.exception.exceptions import InaccurateResponse
from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate

import logging as log


def assert_accuracy(question: str, ai_response: str) -> None:
    """Function responsible for asserting that the question was properly answered.
    :param question: The user question.
    :param ai_response: The AI response to be analysed.
    """
    issues_prompt = PromptTemplate(input_variables=["problems"], template=prompt.read_prompt("assert"))
    if ai_response in msg.accurate_responses:
        return
    elif not ai_response:
        problems = issues_prompt.format(problems="AI provided AN <EMPTY> response")
        raise InaccurateResponse(problems)

    assert_template = PromptTemplate(input_variables=["response", "input"], template=prompt.read_prompt("ryg-rag"))
    final_prompt = assert_template.format(response=ai_response, input=question)
    log.info("Assert::[QUESTION] '%s'  context: '%s'", question, ai_response)
    llm = lc_llm.create_chat_model(Temperature.DATA_ANALYSIS.temp)
    response: AIMessage = llm.invoke(final_prompt)

    if response and (output := response.content):
        if mat := RagResponse.matches(output):
            output: str = output
            status, problems = mat.group(1), mat.group(2)
            log.info("Accuracy check  status: '%s'  reason: '%s'", status, problems)
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.assert_acc(output), verbosity="debug")
            if RagResponse.of_status(status).is_bad:
                problems = issues_prompt.format(problems=RagResponse.strip_code(output))
                raise InaccurateResponse(problems)
            return

    raise InaccurateResponse(f"AI Assistant didn't respond accurately => '{response.content}'")


def resolve_x_refs(ref_name: str, context: str | None) -> str:
    """Replace all cross references by their actual values.
    :param ref_name: The cross-reference or variable name.
    :param context: The context to analyze the references.
    """
    output = ref_name
    if context or (context := str(shared.context.flat("HISTORY"))):
        template = PromptTemplate(input_variables=["history", "pathname"], template=prompt.read_prompt("x-references"))
        final_prompt = template.format(history=context, pathname=ref_name)
        log.info("X-REFS::[QUESTION] %s => CTX: '%s'", ref_name, context)
        llm = lc_llm.create_chat_model(Temperature.DATA_ANALYSIS.temp)
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.x_reference(), verbosity="debug")

        if (result := llm.invoke(final_prompt).content.strip()) and shared.UNCERTAIN_ID not in result:
            output = result

    return output


def check_output(question: str, context: str | None = None) -> str:
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
