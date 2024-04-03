import logging as log
from typing import Optional

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import cache
from askai.core.component.geo_location import geo_location
from askai.core.engine.openai.temperatures import Temperatures
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared


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
    response = chain.invoke({"query": final_prompt, "context": context})

    if response and shared.UNCERTAIN_ID not in response:
        shared.context.push("CONTEXT", f"\n\nUser:\n{query}")
        shared.context.push("CONTEXT", f"\n\nAI:\n{response}", "assistant")
        cache.save_reply(query, response)
        cache.save_query_history()
    else:
        response = msg.translate("Sorry, I don't know.")

    return response


def display(text: str) -> None:
    """Display the given text formatting in markdown."""
    shared.context.push("GENERAL", f"\nAI:{text}\n", "assistant")
    AskAiEvents.ASKAI_BUS.events.reply.emit(message=text)


def stt(question: str, existing_answer: str) -> str:
    """Process the given text according to STT rules."""
    template = PromptTemplate(input_variables=[
        'user', 'idiom', 'question'
    ], template=prompt.read_prompt('stt-prompt'))
    final_prompt = template.format(
        idiom=shared.idiom, answer=existing_answer, question=question
    )

    log.info("STT::[QUESTION] '%s'", existing_answer)
    llm = lc_llm.create_chat_model(temperature=Temperatures.CREATIVE_WRITING.value[0])

    return llm.predict(final_prompt)
