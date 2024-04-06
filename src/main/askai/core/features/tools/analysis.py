import logging as log
from typing import Optional

from langchain_core.prompts import PromptTemplate

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperature import Temperature
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter


def check_output(question: str, context: str) -> Optional[str]:
    """Handle 'Text analysis', invoking: analyze(question: str). Analyze the context and answer the question.
    :param question: The question about the content to be analyzed.
    :param context: The context of the question.
    """
    log.info("Analysis::[QUESTION] '%s'  context=%s", question, context)
    llm = lc_llm.create_chat_model(Temperature.DATA_ANALYSIS.temp)
    template = PromptTemplate(
        input_variables=['context', 'question'],
        template=prompt.read_prompt('qstring-prompt'))
    final_prompt = template.format(context=context, question=question)

    if output := llm.predict(final_prompt):
        shared.context.set("ANALYSIS", question)
        shared.context.push("ANALYSIS", output, 'assistant')
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.analysis(output))

    return text_formatter.ensure_ln(output)


def stt(question: str, existing_answer: str) -> str:
    """Process the given text according to STT rules."""
    template = PromptTemplate(input_variables=[
        'user', 'idiom', 'question'
    ], template=prompt.read_prompt('stt-prompt'))
    final_prompt = template.format(
        idiom=shared.idiom, answer=existing_answer, question=question
    )
    log.info("STT::[QUESTION] '%s'", existing_answer)
    llm = lc_llm.create_chat_model(temperature=Temperature.CREATIVE_WRITING.temp)

    if output := llm.predict(final_prompt):
        shared.context.set("ANALYSIS", question)
        shared.context.push("ANALYSIS", output, 'assistant')

    return text_formatter.ensure_ln(output)
