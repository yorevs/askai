import logging as log
from typing import Optional

from hspylib.core.tools.text_tools import ensure_endswith
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import cache
from askai.core.component.geo_location import geo_location
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
    output = chain.invoke({"query": final_prompt, "context": context})

    if output and shared.UNCERTAIN_ID not in output:
        shared.context.push("GENERAL", f"\n\nUser:\n{query}")
        shared.context.push("GENERAL", f"\nAI:\n{output}", "assistant")
        cache.save_reply(query, output)
        cache.save_query_history()
    else:
        output = msg.translate("Sorry, I don't know.")

    return ensure_endswith(output, '\n\n')


def display(text: str) -> None:
    """Display the given text formatting in markdown."""
    shared.context.push("GENERAL", f"\nAI:{text}\n", "assistant")
    AskAiEvents.ASKAI_BUS.events.reply.emit(message=text)
