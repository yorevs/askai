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
from askai.core.component.cache_service import cache
from askai.core.engine.openai.temperature import Temperature
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import extract_codeblock
from hspylib.core.config.path_object import PathObject
from hspylib.core.preconditions import check_not_none
from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate
from pathlib import Path

import logging as log


def generate_content(description: str, mime_type: str, path_name: str | None) -> str:
    """Generate content using the AI. It's a general function now, but ican be specialized afterwards.
    :param description: The description to use to generate the content.
    :param mime_type: The content type and format using MIME types.
    :param path_name: The directory path where you want to save the generated content.
    """
    check_not_none((description, mime_type, path_name))
    template = PromptTemplate(input_variables=["mime_type", "input"], template=prompt.read_prompt("generator"))
    final_prompt = template.format(mime_type=mime_type, input=description)

    log.info("GENERATE::[PROMPT] '%s'  Type: '%s'  Path: '%s'", description, mime_type, path_name)
    llm = lc_llm.create_chat_model(temperature=Temperature.CODE_GENERATION.temp)
    response: AIMessage = llm.invoke(final_prompt)

    if response and (output := response.content):
        shared.context.push("HISTORY", output, "assistant")
        if path_name:
            path_obj = PathObject.of(path_name)
            base_dir = path_obj.abs_dir
            if Path(base_dir).exists:
                with open(path_obj.join(), "w") as f_path_name:
                    _, content = extract_codeblock(output)
                    f_path_name.write(content)
        cache.save_reply(prompt, output)
    else:
        output = msg.translate("Sorry, I don't know.")

    return output or msg.translate("Sorry, the prompt produced no content!")
