import logging as log
from typing import Optional

from hspylib.core.tools.text_tools import ensure_endswith
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared


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
        shared.context.push("CONTEXT", f"\n\nAI:\n{output}", "assistant")

    return ensure_endswith(output, '\n\n')
