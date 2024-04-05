import logging as log
import os
import re
from typing import Optional

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

from askai.core.askai_configs import configs
from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import cache
from askai.core.component.geo_location import geo_location
from askai.core.engine.openai.temperature import Temperature
from askai.core.model.rag_response import RagResponse
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter
from askai.core.support.utilities import display_text
from askai.exception.exceptions import InaccurateResponse


def fetch(query: str) -> Optional[str]:
    """Fetch the information from the AI Database."""
    template = PromptTemplate(input_variables=[
        'user', 'idiom', 'question'
    ], template=prompt.read_prompt('generic-prompt'))
    final_prompt = template.format(
        user=shared.username, question=query,
        idiom=shared.idiom, datetime=geo_location.datetime
    )
    ctx: str = shared.context.flat("GENERAL", "INTERNET")
    log.info("FETCH::[QUESTION] '%s'  context: '%s'", query, ctx)
    chat_prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
    chain = create_stuff_documents_chain(lc_llm.create_chat_model(), chat_prompt)
    context = [Document(ctx)]
    output = chain.invoke({"query": final_prompt, "context": context})

    if output and shared.UNCERTAIN_ID not in output:
        shared.context.push("GENERAL", f"\n\nUser:\n{query}")
        shared.context.push("GENERAL", f"\nAI:\n{output}", "assistant")
        cache.save_reply(query, output)
    else:
        output = msg.translate("Sorry, I don't know.")

    return text_formatter.ensure_ln(output)


def display(*texts: str) -> Optional[str]:
    """Display the given text formatting in markdown."""
    messages: str = os.linesep.join(texts)
    if configs.is_interactive:
        if not re.match(r'^%[a-zA-Z0-9_-]+%$', messages):
            shared.context.push("GENERAL", f"\nAI:{messages}\n", "assistant")
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=messages)
    else:
        display_text(messages, f"{shared.nickname}: ")

    return messages


def assert_accuracy(question: str, ai_response: str) -> None:
    """Function responsible for asserting that the question was properly answered."""
    if ai_response:
        template = PromptTemplate(
            input_variables=['question', 'response'],
            template=prompt.read_prompt('rag-prompt'))
        final_prompt = template.format(question=question, response=ai_response or '')
        llm = lc_llm.create_chat_model(Temperature.DATA_ANALYSIS.temp)
        if (output := llm.predict(final_prompt)) and (mat := RagResponse.matches(output)):
            status, reason = mat.group(1), mat.group(2)
            log.info(
                "Asserting accuracy of question '%s' resulted in: '%s' -> '%s'",
                question, status, reason)
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.assert_acc(question, output), verbosity='debug')
            if RagResponse.of_value(status.strip()).is_bad:
                raise InaccurateResponse(f"The AI response for the question was: '{output}' ")
            return

    raise InaccurateResponse(f"The AI response was not Green")
