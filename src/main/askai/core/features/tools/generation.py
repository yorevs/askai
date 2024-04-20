import os

from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import cache
from askai.core.engine.openai.temperature import Temperature
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from hspylib.core.preconditions import check_not_none
from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate
from os.path import dirname, basename
from pathlib import Path

import logging as log

from askai.core.support.utilities import extract_codeblock


def generate_content(description: str, mime_type: str, pathname: str | None) -> str:
    """Generate content using the AI. It's a general function now, but ican be specialized afterwards.
    :param description: The description to use to generate the content.
    :param mime_type: The content type and format using MIME types.
    :param pathname: The directory path where you want to save the generated content.
    """
    check_not_none((description, mime_type, pathname))
    template = PromptTemplate(input_variables=["mime_type", "input"], template=prompt.read_prompt("generator"))
    final_prompt = template.format(mime_type=mime_type, input=description)

    log.info("GENERATE::[PROMPT] '%s'  Type: '%s'  Path: '%s'", description, mime_type, pathname)
    llm = lc_llm.create_chat_model(temperature=Temperature.CODE_GENERATION.temp)
    response: AIMessage = llm.invoke(final_prompt)

    if response and (output := response.content):
        shared.context.push("HISTORY", output, "assistant")
        if pathname:
            base_dir = Path(dirname(pathname.replace("~", os.getenv("HOME"))))
            filename = basename(pathname)
            if base_dir.is_dir() and base_dir.exists():
                with open(f"{base_dir}/{filename}", "w") as f_path_name:
                    _, content = extract_codeblock(output)
                    f_path_name.write(content)
        cache.save_reply(prompt, output)
    else:
        output = msg.translate("Sorry, I don't know.")

    return output or msg.translate("Sorry, the prompt produced no content!")
