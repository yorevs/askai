from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import cache
from askai.core.engine.openai.temperature import Temperature
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from hspylib.core.preconditions import check_not_none
from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate
from os.path import dirname
from pathlib import Path

import logging as log


def generate_content(description: str, mime_type: str, path_name: str | None) -> str:
    """Display the given texts formatted with markdown.
    :param description: Specify the prompt to be used to generate the content.
    :param mime_type: Specify the content type and format using MIME types.
    :param path_name: Specify the directory path where you want to save the generated content.
    """
    check_not_none((description, mime_type, path_name))
    output = None
    template = PromptTemplate(input_variables=["mime_type", "input"], template=prompt.read_prompt("generator-prompt"))
    final_prompt = template.format(mime_type=mime_type, input=description)

    log.info("GENERATE::[PROMPT] '%s'  Type: '%s'  Path: '%s'", description, mime_type, path_name)
    llm = lc_llm.create_chat_model(temperature=Temperature.CODE_GENERATION.temp)
    response: AIMessage = llm.invoke(final_prompt)

    if response and (output := response.content):
        shared.context.push("HISTORY", output, "assistant")
        if path_name:
            base_dir = Path(dirname(path_name))
            if base_dir.is_dir() and base_dir.exists():
                with open(path_name, "w") as f_path_name:
                    f_path_name.write(output)
        cache.save_reply(prompt, output)
    else:
        output = msg.translate("Sorry, I don't know.")

    return output or msg.translate("Sorry, the prompt produced no content!")
