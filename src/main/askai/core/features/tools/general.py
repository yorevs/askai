import logging as log
import os
from typing import Optional

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import cache
from askai.core.engine.openai.temperature import Temperature
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared


def display(*texts: str) -> Optional[str]:
    """Display the given texts formatted with markdown.
    :param texts: The texts to be displayed.
    """
    if output := os.linesep.join(texts):
        shared.context.push("HISTORY", output, 'assistant')

    return output or msg.translate("Sorry, there is nothing to display")


def final_answer(question: str, context: str | None) -> Optional[str]:
    """Fetch the information from the AI Database.
    :param question: The user question.
    :param context: The final AI response or context.
    """
    template = PromptTemplate(input_variables=[
        'user', 'idiom', 'context', 'question'
    ], template=prompt.read_prompt('taius-prompt'))
    final_prompt = template.format(
        user=prompt.user.title(), idiom=shared.idiom,
        context=context, question=question)
    ctx: str = shared.context.flat("HISTORY")
    log.info("FETCH::[QUESTION] '%s'  context: '%s'", question, ctx)
    llm = lc_llm.create_chat_model(temperature=Temperature.EXPLORATORY_CODE_WRITING.temp)

    chat_prompt = ChatPromptTemplate.from_messages([("system", "{context}\n\n{query}")])
    chain = create_stuff_documents_chain(llm, chat_prompt)
    context = [Document(str(ctx))]

    if (output := chain.invoke({"query": final_prompt, "context": context})) and shared.UNCERTAIN_ID not in output:
        shared.context.push("HISTORY", output, 'assistant')
        cache.save_reply(question, output)
    else:
        output = msg.translate("Sorry, I don't know.")

    return output


def stt_response(question: str, context: str) -> str:
    """Process the given context according to STT rules.
    :param question: The question about the content to be summarized.
    :param context: The non-stt response context.
    """
    output = None
    if not context:
        context = str(shared.context.flat("HISTORY"))
    template = PromptTemplate(input_variables=[
        'idiom', 'context', 'question'
    ], template=prompt.read_prompt('stt-prompt'))
    final_prompt = template.format(
        idiom=shared.idiom, context=context, question=question
    )
    log.info("STT::[QUESTION] '%s'", context)
    llm = lc_llm.create_chat_model(temperature=Temperature.CODE_COMMENT_GENERATION.temp)

    if (response := llm.invoke(final_prompt)) and (output := response.content):
        shared.context.push("HISTORY", output, 'assistant')
        output = response.content

    return output or msg.translate("Sorry, there is nothing to show")
