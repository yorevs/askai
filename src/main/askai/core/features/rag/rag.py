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
from langchain_core.prompts import PromptTemplate

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperature import Temperature
from askai.core.model.rag_response import RagResponse
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.exception.exceptions import InaccurateResponse


def assert_accuracy(question: str, ai_response: str) -> None:
    """Function responsible for asserting that the question was properly answered.
    :param question: The user question.
    :param ai_response: The AI response to be analysed.
    """
    issues_prompt = PromptTemplate(input_variables=["problems"], template=prompt.read_prompt("assert"))
    if ai_response in msg.accurate_responses:
        return
    elif not ai_response:
        empty_msg = "AI provided AN <EMPTY> response"
        problems = issues_prompt.format(problems=empty_msg)
        shared.context.push("SCRATCHPAD", issues_prompt.format(problems=RagResponse.strip_code(empty_msg)))
        raise InaccurateResponse(problems)

    assert_template = PromptTemplate(input_variables=["response", "input"], template=prompt.read_prompt("rag"))
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
                shared.context.push("SCRATCHPAD", issues_prompt.format(problems=RagResponse.strip_code(output)))
                raise InaccurateResponse(f"AI Assistant didn't respond accurately => '{response.content}'")
            return

    raise InaccurateResponse(f"AI Assistant didn't respond accurately => '{response.content}'")


def resolve_x_refs(ref_name: str, context: str | None) -> str:
    """Replace all cross references by their actual values.
    :param ref_name: The cross-reference or variable name.
    :param context: The context to analyze the references.
    """
    output = ref_name
    if context or (context := str(shared.context.flat("HISTORY"))):
        template = PromptTemplate(input_variables=["context", "pathname"], template=prompt.read_prompt("x-references"))
        final_prompt = template.format(context=context, pathname=ref_name)
        log.info("X-REFS::[QUESTION] %s => CTX: '%s'", ref_name, context)
        llm = lc_llm.create_chat_model(Temperature.DATA_ANALYSIS.temp)
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.x_reference(), verbosity="debug")

        if (result := llm.invoke(final_prompt).content.strip()) and shared.UNCERTAIN_ID not in result:
            output = result

    return output


def final_answer(
    question: str,
    username: str = prompt.user.title(),
    idiom: str = shared.idiom,
    persona_prompt: str = "taius",
    response: str = None,
) -> str:
    """Provide the final response to the user.
    :param question: The user question.
    :param username: The user name.
    :param idiom: The determined user idiom.
    :param persona_prompt: The persona prompt to be used.
    :param response: The final AI response or context.
    """
    output = response
    if response:
        template = PromptTemplate(
            input_variables=["user", "idiom", "context", "question"],
            template=prompt.read_prompt(persona_prompt)
        )
        final_prompt = template.format(user=username, idiom=idiom, context=response, question=question)
        log.info("FETCH::[QUESTION] '%s'  context: '%s'", question, response)
        llm = lc_llm.create_chat_model(temperature=Temperature.CODE_GENERATION.temp)
        response: AIMessage = llm.invoke(final_prompt)

        if not response or not (output := response.content) or shared.UNCERTAIN_ID in response.content:
            output = msg.translate("Sorry, I was not able to provide a helpful response.")

    return output or msg.translate("Sorry, the query produced no response!")
