import logging as log
from functools import lru_cache
from string import Template
from typing import Optional

from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperature import Temperature
from askai.core.model.rag_response import RagResponse
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter
from askai.exception.exceptions import InaccurateResponse

ASSERT_MSG: Template = Template(
    "The AI provided {reason} answer\n"
    "Please try again improving your response. Address the problems above.\n(Reminder "
    "to respond using at least one tool, stick to the tools syntax and avoid responding directly).\n"
)


def assert_accuracy(question: str, ai_response: str) -> str:
    """Function responsible for asserting that the question was properly answered.
    :param question: The user question.
    :param ai_response: The AI response to be analysed.
    """
    if ai_response in msg.accurate_responses:
        return ai_response
    elif not ai_response:
        reason = ASSERT_MSG.substitute(reason='AN EMPTY')
        shared.context.push("CONTEXT", reason)
        raise InaccurateResponse(f"AI Assistant didn't respond accurately => 'EMPTY'")

    template = PromptTemplate(
        input_variables=['response', 'question'],
        template=prompt.read_prompt('ryg-prompt'))
    final_prompt = template.format(response=ai_response, question=question)
    log.info("Assert::[QUESTION] '%s'  context: '%s'", question, ai_response)
    llm = lc_llm.create_chat_model(Temperature.DATA_ANALYSIS.temp)
    response: AIMessage = llm.invoke(final_prompt)

    if response and (output := response.content):
        if mat := RagResponse.matches(output):
            output: str = output
            status, reason = mat.group(1), mat.group(2)
            log.info("Accuracy check  status: '%s'  reason: '%s'", status, reason)
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.assert_acc(output), verbosity='debug')
            if RagResponse.of_status(status).is_bad:
                shared.context.push("CONTEXT", ASSERT_MSG.substitute(reason='A BAD'))
                raise InaccurateResponse(RagResponse.strip_code(output))
            return ai_response

    raise InaccurateResponse(f"AI Assistant didn't respond accurately => '{response.content}'")


@lru_cache
def check_output(question: str, context: str | None) -> str:
    """Handle 'Text analysis', invoking: analyze(question: str). Analyze the context and answer the question.
    :param question: The question about the content to be analyzed.
    :param context: The context of the question.
    """
    if not context:
        context = str(shared.context.flat("CONTEXT"))
    log.info("Analysis::[QUESTION] '%s'  context=%s", question, context)
    llm = lc_llm.create_chat_model(Temperature.DATA_ANALYSIS.temp)
    template = PromptTemplate(
        input_variables=['context', 'question'],
        template=prompt.read_prompt('analysis-prompt'))
    final_prompt = template.format(context=context, question=question)
    AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.analysis(), verbosity='debug')
    response = llm.invoke(final_prompt)

    if response and (output := response.content):
        shared.context.push("CONTEXT", question)
        shared.context.push("CONTEXT", output, 'assistant')
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.analysis_done(output), verbosity='debug')
        return text_formatter.ensure_ln(output)

    return "Error: Nothing has been analyzed!"


def replace_x_refs(question: str, context: str) -> Optional[str]:
    """Replace all cross references by their actual values.
    :param question: The original useer question.
    :param context: The context to analyze the references.
    """
    template = PromptTemplate(input_variables=[
        'history', 'question'
    ], template=prompt.read_prompt('x-references-prompt'))
    final_prompt = template.format(
        history=context, question=question)
    log.info("X-REFS::[QUESTION] %s => CTX: '%s'", question, context)
    llm = lc_llm.create_chat_model(Temperature.DATA_ANALYSIS.temp)
    AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.x_reference(), verbosity='debug')

    return llm.invoke(final_prompt).content.strip()


@lru_cache
def stt(question: str, context: str) -> str:
    """Process the given context according to STT rules.
    :param question: The question about the content to be summarized.
    :param context: The non-stt response context.
    """
    if context:
        template = PromptTemplate(input_variables=[
            'idiom', 'context', 'question'
        ], template=prompt.read_prompt('stt-prompt'))
        final_prompt = template.format(
            idiom=shared.idiom, context=context, question=question
        )
        log.info("STT::[QUESTION] '%s'", context)
        llm = lc_llm.create_chat_model(temperature=Temperature.CREATIVE_WRITING.temp)

        if output := llm.invoke(final_prompt):
            shared.context.push("CONTEXT", question)
            shared.context.push("CONTEXT", output, 'assistant')
            return text_formatter.ensure_ln(output)

    return "Error: Context or LLM response is empty!"
