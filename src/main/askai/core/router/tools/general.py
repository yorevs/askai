#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.router.tools.general
      @file: general.py
   @created: Mon, 01 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperature import Temperature
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from hspylib.core.config.path_object import PathObject
from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate

import os


def display_tool(*texts: str) -> str:
    """Display the given texts using markdown.
    :param texts: The list of texts to be displayed.
    """
    output = os.linesep.join(texts)

    return output or "Sorry, there is nothing to display"


def final_answer(persona_prompt: str | None = None, input_variables: list[str] | None = None, **prompt_args) -> str:
    """Provide the final response to the user.
    :param persona_prompt: The persona prompt to be used.
    :param input_variables: The prompt input variables.
    :param prompt_args: The prompt input arguments.
    """
    prompt_file: PathObject = PathObject.of(prompt.append_path(f"taius/{persona_prompt}"))
    # fmt: off
    template = PromptTemplate(
        input_variables=input_variables or [],
        template=prompt.read_prompt(prompt_file.filename, prompt_file.abs_dir)
    )
    # fmt: on
    final_prompt = template.format(**prompt_args)
    llm = lc_llm.create_chat_model(temperature=Temperature.COLDEST.temp)
    response: AIMessage = llm.invoke(final_prompt)
    output: str | None = None

    if not response or not (output := response.content) or shared.UNCERTAIN_ID in response.content:
        output = "Sorry, I was not able to provide a helpful response."

    return output or "Sorry, the query produced no response!"
