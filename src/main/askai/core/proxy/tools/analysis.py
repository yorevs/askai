import logging as log
from typing import Optional

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

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
    chat_prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
    chain = create_stuff_documents_chain(lc_llm.create_chat_model(), chat_prompt)
    context = [Document(context)]

    if output := chain.invoke({"query": question, "context": context}):
        shared.context.set("ANALYSIS", f"\n\nUser:\n{question}")
        shared.context.push("ANALYSIS", f"\nAI:\n{output}", "assistant")

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
        shared.context.set("ANALYSIS", f"\n\nUser:\n{question}")
        shared.context.push("ANALYSIS", f"\nAI:\n{output}", "assistant")

    return text_formatter.ensure_ln(output)
