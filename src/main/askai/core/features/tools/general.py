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
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter
from askai.core.support.utilities import display_text


def fetch(question: str) -> Optional[str]:
    """Fetch the information from the AI Database."""
    template = PromptTemplate(input_variables=[
        'user', 'idiom', 'question'
    ], template=prompt.read_prompt('generic-prompt'))
    final_prompt = template.format(
        user=shared.username, question=question,
        idiom=shared.idiom, datetime=geo_location.datetime)
    ctx: str = shared.context.flat("GENERAL", "INTERNET")
    log.info("FETCH::[QUESTION] '%s'  context: '%s'", question, ctx)
    chat_prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
    chain = create_stuff_documents_chain(lc_llm.create_chat_model(), chat_prompt)
    context = [Document(ctx)]

    output = chain.invoke({"query": final_prompt, "context": context})
    if output and shared.UNCERTAIN_ID not in output:
        cache.save_reply(question, output)
    else:
        output = msg.translate("Sorry, I don't know.")

    return text_formatter.ensure_ln(output)


def display(*texts: str) -> Optional[str]:
    """Display the given texts formatted with markdown."""
    output: str = os.linesep.join(texts)
    if configs.is_interactive:
        if not re.match(r'^%[a-zA-Z0-9_-]+%$', output):
            shared.context.push("GENERAL", output, 'assistant')
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=output)
    else:
        display_text(output, f"{shared.nickname}: ")

    return output
