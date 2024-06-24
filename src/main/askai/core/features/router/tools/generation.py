#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.features.tools.generation
      @file: generation.py
   @created: Mon, 01 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperature import Temperature
from askai.core.support.langchain_support import lc_llm
from askai.core.support.utilities import extract_codeblock
from hspylib.core.config.path_object import PathObject
from hspylib.core.preconditions import check_not_none
from hspylib.core.tools.text_tools import ensure_endswith
from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate
from pathlib import Path

import logging as log
import os


def generate_content(query: str, mime_type: str, path_name: str | None) -> str:
    """Generate and save content using the AI. It's a general function now, but it can be specialized afterwards.
    :param query: The description to use to generate the content.
    :param mime_type: The content type and format using MIME types.
    :param path_name: The directory path where you want to save the generated content.
    """
    check_not_none((query, mime_type, path_name))
    template = PromptTemplate(input_variables=["mime_type", "input"], template=prompt.read_prompt("generator"))
    final_prompt: str = template.format(mime_type=mime_type, input=query)
    output: str = ''

    log.info("GENERATE::[PROMPT] '%s'  Type: '%s'  Path: '%s'", query, mime_type, path_name)
    llm = lc_llm.create_chat_model(temperature=Temperature.CODE_GENERATION.temp)
    response: AIMessage = llm.invoke(final_prompt)

    if response and (output := response.content):
        if path_name:
            path_obj = PathObject.of(path_name)
            base_dir = path_obj.abs_dir
            if Path(base_dir).exists:
                filename: str = path_obj.join()
                with open(filename, "w") as f_path_name:
                    lang, content = extract_codeblock(output)
                    f_path_name.write(ensure_endswith(content, os.linesep))
                    output = msg.translate(
                        f"{lang.title()} content successfully saved as: '{filename}'\n\n```{lang}\n{content}\n")
            else:
                output = msg.translate(f"Sorry, the AI was unable save the content at: '{path_name}' !")

    return output or msg.translate("Sorry, the AI was unable to generate any content!")
