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
from askai.core.component.rag_provider import RAGProvider
from askai.core.engine.openai.temperature import Temperature
from askai.core.enums.acc_color import AccColor
from askai.core.model.acc_response import AccResponse
from askai.core.model.ai_reply import AIReply
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.exception.exceptions import InaccurateResponse, InterruptionRequest, TerminatingQuery
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from textwrap import dedent

import logging as log

# fmt: off
EVALUATION_GUIDE: str = dedent("""
**Accuracy Evaluation Guidelines:**

1. Analyze past responses to ensure accuracy.
2. Regularly self-critique overall responses.
3. Reflect on past strategies to refine your approach.
4. Experiment with different methods or solutions.
""").strip()
# fmt: on

RAG: RAGProvider = RAGProvider("accuracy.csv")


def assert_accuracy(question: str, ai_response: str, pass_threshold: AccColor = AccColor.MODERATE) -> AccResponse:
    """Assert that the AI's response to the question meets the required accuracy threshold.
    :param question: The user's question.
    :param ai_response: The AI's response to be analyzed for accuracy.
    :param pass_threshold: The accuracy threshold, represented by a color, that must be met or exceeded for the
                           response to be considered a pass (default is AccResponse.MODERATE).
    :return: The accuracy classification of the AI's response as an AccResponse enum value.
    """
    if ai_response and ai_response not in msg.accurate_responses:
        acc_template = PromptTemplate(input_variables=["problems"], template=prompt.read_prompt("acc-report"))
        eval_template = PromptTemplate(
            input_variables=["rag", "input", "response"], template=prompt.read_prompt("evaluation")
        )
        final_prompt = eval_template.format(rag=RAG.get_rag_examples(question), input=question, response=ai_response)
        log.info("Assert::[QUESTION] '%s'  context: '%s'", question, ai_response)
        llm = lc_llm.create_chat_model(Temperature.COLDEST.temp)
        response: AIMessage = llm.invoke(final_prompt)

        if response and (output := response.content):
            if acc := AccResponse.parse_response(output):
                log.info("Accuracy check ->  status: '%s'  details: '%s'", acc.status, acc.details)
                events.reply.emit(reply=AIReply.debug(msg.assert_acc(acc.status, acc.details)))
                if acc.is_interrupt:
                    # AI flags that it can't continue interacting.
                    log.warning(msg.interruption_requested(output))
                    raise InterruptionRequest(ai_response)
                elif acc.is_terminate:
                    # AI flags that the user wants to end the session.
                    raise TerminatingQuery(ai_response)
                elif not acc.is_pass(pass_threshold):
                    # Include the guidelines for the first mistake.
                    if not shared.context.get("EVALUATION"):
                        shared.context.push("EVALUATION", EVALUATION_GUIDE)
                    shared.context.push("EVALUATION", acc_template.format(problems=acc.details))
                    raise InaccurateResponse(f"AI Assistant failed to respond => '{response.content}'")
                return acc
        # At this point, the response was inaccurate.
        raise InaccurateResponse(f"AI Assistant didn't respond accurately. Response: '{response}'")


def resolve_x_refs(ref_name: str, context: str | None = None) -> str:
    """Replace all cross-references with their actual values.
    :param ref_name: The name of the cross-reference or variable to resolve.
    :param context: The context in which to analyze and resolve the references (optional).
    :return: The string with all cross-references replaced by their corresponding values.
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
        events.reply.emit(reply=AIReply.debug(msg.x_reference(ref_name)))
        response = runnable.invoke({"pathname": ref_name}, config={"configurable": {"session_id": "HISTORY"}})
        if response and (output := response.content) and shared.UNCERTAIN_ID != output:
            output = response.content

    return output
