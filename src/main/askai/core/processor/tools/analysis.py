import logging as log
from typing import Optional

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.tools import tool

from askai.core.askai_prompt import prompt
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared


@tool
def analyze_output(question: str) -> Optional[str]:
    """Check or Analyze any llm output or text, provided the question.
    :param question: The question about the output to be analyzed.
    """
    template = PromptTemplate(
        input_variables=["idiom"],
        template=prompt.read_prompt("analysis-prompt"))
    final_prompt: str = template.format(idiom=shared.idiom, question=question)
    ctx: str = shared.context.flat("CONTEXT", "OUTPUT")
    log.info("Analysis::[QUESTION] '%s'  context=%s", final_prompt, ctx)

    chat_prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
    chain = create_stuff_documents_chain(lc_llm.create_chat_model(), chat_prompt)
    context = [Document(ctx)]

    if response := chain.invoke({"query": final_prompt, "context": context}):
        log.debug("Analysis::[RESPONSE] Received from AI: %s.", response)
        if response and shared.UNCERTAIN_ID not in response:
            shared.context.push("CONTEXT", f"\n\nUser:\n{question}")
            shared.context.push("CONTEXT", f"\n\nAI:\n{response}", "assistant")
        else:
            response = "I DON't KNOW"
    else:
        log.error(f"Analysis processing failed. CONTEXT=%s  RESPONSE=%s", context, response)

    return response
