import logging as log
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


def display(text: str) -> None:
    """Display the given text formatting in markdown."""
    if configs.is_interactive:
        shared.context.push("GENERAL", f"\nAI:{text}\n", "assistant")
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=text)
    else:
        display_text(text, f"{shared.nickname}: ")


def assert_accuracy(question: str, ai_response: str) -> Optional[str]:
    """Function responsible for asserting that the question was properly answered."""
    if ai_response:
        template = PromptTemplate(
            input_variables=['question', 'response'],
            template=prompt.read_prompt('rag-prompt'))
        final_prompt = template.format(question=question, response=ai_response)
        llm = lc_llm.create_chat_model(Temperature.DATA_ANALYSIS.temp)
        output = llm.predict(final_prompt)
        log.info(
            "Asserting accuracy of question '%s' using response '%s' resulted in: '%s'",
            question, ai_response, output)
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.assert_acc(question, output), verbosity='debug')
        if RagResponse.of_value(output).is_bad:
            raise InaccurateResponse(f"The response was '{output}' for the question: '{question}'")
