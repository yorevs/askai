import logging as log
from textwrap import dedent

from hspylib.core.preconditions import check_not_none
from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate

from askai.core.askai_messages import msg
from askai.core.component.cache_service import cache
from askai.core.engine.openai.temperature import Temperature
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared

GENERATION_TEMPLATE = PromptTemplate(
    input_variables=[
        'mime_type', 'input'
    ], template=dedent(
        """
        You are a highly sophisticated GPT tailored for creating '{mime_type}' content. Please be as accurate as possible while
        creating the content. Ensure that your content has a good quality. To create the content use the following prompt:

        {input}
        """
    ))


def generate_content(prompt: str, mime_type: str, path_name: str) -> str:
    """Display the given texts formatted with markdown.
    :param prompt: Specify the prompt to be used to generate the content.
    :param mime_type: Specify the content type and format using MIME types.
    :param path_name: Specify the directory path where you want to save the generated content.
    """
    check_not_none((prompt, mime_type, path_name))
    output = None
    template = GENERATION_TEMPLATE
    final_prompt = template.format(
        mime_type=mime_type, input=input)

    log.info("GENERATE::[PROMPT] '%s'  Type: '%s'  Path: '%s'", prompt, mime_type, path_name)
    llm = lc_llm.create_chat_model(temperature=Temperature.CODE_GENERATION.temp)
    response: AIMessage = llm.invoke(final_prompt)

    if response and (output := response.content) and shared.UNCERTAIN_ID not in response.content:
        shared.context.push("HISTORY", output, 'assistant')
        cache.save_reply(prompt, output)
    else:
        output = msg.translate("Sorry, I don't know.")

    return output or msg.translate("Sorry, the prompt produced no content!")
