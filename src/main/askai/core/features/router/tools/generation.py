#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.features.tools.generation
      @file: generation.py
   @created: Mon, 01 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperature import Temperature
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import extract_codeblock
from hspylib.core.config.path_object import PathObject
from hspylib.core.metaclass.classpath import AnyPath
from hspylib.core.preconditions import check_not_none
from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate
from pathlib import Path
from typing import AnyStr

import logging as log
import os


def generate_content(prompt_str: str, mime_type: str) -> str:
    """Generate content using the AI. It's a general function now, but it can be specialized afterwards.
    :param prompt_str: The prompt (instructions) to generate the content.
    :param mime_type: The content type and format using MIME types.
    """
    check_not_none((prompt_str, mime_type))
    template = PromptTemplate(input_variables=["mime_type", "input"], template=prompt.read_prompt("generator"))
    final_prompt: str = template.format(mime_type=mime_type, input=prompt_str)
    output: str = ""
    prompt_str += "\nFormat the content into a markdown code block.\n"

    log.info("GENERATE::[PROMPT] '%s'  Type: '%s'", prompt_str, mime_type)
    llm = lc_llm.create_chat_model(temperature=Temperature.CODE_GENERATION.temp)
    response: AIMessage = llm.invoke(final_prompt)

    if response and (output := response.content):
        shared.context.set("GENERATED", output)
    else:
        output = msg.no_output("GenAI")

    return f"The following '{mime_type}' content was generated.\n\n{output}\n"


def save_content(filepath: AnyPath, content: AnyStr = None) -> str:
    """Save any generated context into a file.
    :param filepath: The path where you want to save the content.
    :param content: The content to be saved. If not provided, it will get from the last generated context.
    """
    if filepath:
        path_obj = PathObject.of(filepath)
        base_dir = path_obj.abs_dir
        if Path(base_dir).exists and (output := str(content or shared.context.flat("GENERATED"))):
            filename: str = path_obj.join()
            with open(filename, "w") as f_path_name:
                lang, content = extract_codeblock(output)
                f_path_name.write(f"\n{content}\n")
                output = f"{lang.title()} content successfully saved as: '{filename}'\n"
        if not os.path.exists(filepath):
            output = f"Sorry, the AI was unable save the content at: '{filepath}' !"
    else:
        output = f"File path '{filepath}' was not found !"

    return output
