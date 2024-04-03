import logging as log
from typing import Optional

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import cache
from askai.core.component.geo_location import geo_location
from askai.core.component.internet_service import internet
from askai.core.model.search_result import SearchResult
from askai.core.support.langchain_support import lc_llm
from askai.core.support.object_mapper import object_mapper
from askai.core.support.shared_instances import shared


def browse(query: str) -> Optional[str]:
    """Fetch the information from the Internet."""
    template = PromptTemplate(input_variables=[
        "idiom", "datetime", 'location', 'question'
    ], template=prompt.read_prompt('internet-prompt'))
    final_prompt: str = template.format(
        idiom=shared.idiom, datetime=geo_location.datetime,
        location=geo_location.location, question=query)

    log.info("Browser::[QUESTION] '%s'  context=''", final_prompt)

    chat_prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
    chain = create_stuff_documents_chain(lc_llm.create_chat_model(), chat_prompt)
    context = []

    response = chain.invoke({"query": final_prompt, "context": context})
    if response and shared.UNCERTAIN_ID not in response:
        search: SearchResult = object_mapper.of_json(response, SearchResult)
        if not isinstance(search, SearchResult):
            log.error(msg.invalid_response(search))
            output = response.strip()
        else:
            if output := internet.search_google(search):
                output = msg.translate(output)
                shared.context.set("INTERNET", f"\nAI:\n{output}", "assistant")
                cache.save_reply(query, output)
            else:
                output = msg.search_empty()
    else:
        output = msg.translate("Sorry, I don't know.")

    return f"\n{output}\n"
