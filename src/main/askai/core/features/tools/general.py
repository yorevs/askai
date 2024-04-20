from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import cache
from askai.core.engine.openai.temperature import Temperature
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate

import logging as log
import os


def display_tool(*texts: str) -> str:
    """Display the given texts using markdown.
    :param texts: The list of texts to be displayed.
    """
    if output := os.linesep.join(texts):
        shared.context.push("HISTORY", output, "assistant")

    return output or msg.translate("Sorry, there is nothing to display")


def final_answer(
    question: str,
    username: str = prompt.user.title(),
    idiom: str = shared.idiom,
    persona: str = "taius",
    context: str | None = None,
) -> str:
    """Provide the final response to the user.
    :param question: The user question.
    :param username: The user name.
    :param idiom: The determined user idiom.
    :param persona: The persona prompt to be used.
    :param context: The final AI response or context.
    """
    output = None
    if not context:
        context: str = str(shared.context.flat("HISTORY"))
    template = PromptTemplate(
        input_variables=["user", "idiom", "context", "question"], template=prompt.read_prompt(persona)
    )
    final_prompt = template.format(user=username, idiom=idiom, context=context, question=question)

    log.info("FETCH::[QUESTION] '%s'  context: '%s'", question, context)
    llm = lc_llm.create_chat_model(temperature=Temperature.EXPLORATORY_CODE_WRITING.temp)
    response: AIMessage = llm.invoke(final_prompt)

    if response and (output := response.content) and shared.UNCERTAIN_ID not in response.content:
        shared.context.push("HISTORY", output, "assistant")
        cache.save_reply(question, output)
    else:
        output = msg.translate("Sorry, I don't know.")

    return output or msg.translate("Sorry, the query produced no response!")
