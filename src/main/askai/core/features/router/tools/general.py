#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.features.tools.general
      @file: general.py
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
from askai.core.support.shared_instances import shared
from hspylib.core.config.path_object import PathObject
from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate

import logging as log
import os


def display_tool(*texts: str) -> str:
    """Display the given texts using markdown.
    :param texts: The list of texts to be displayed.
    """
    output = os.linesep.join(texts)

    return output or msg.translate("Sorry, there is nothing to display")

def final_answer(
    question: str,
    username: str = prompt.user.title(),
    idiom: str = shared.idiom,
    persona_prompt: str | None = None,
    response: str | None = None,
) -> str:
    """Provide the final response to the user.
    :param question: The user question.
    :param username: The user name.
    :param idiom: The determined user idiom.
    :param persona_prompt: The persona prompt to be used.
    :param response: The final AI response or context.
    """
    output = response or ""
    prompt_file: PathObject = PathObject.of(prompt.append_path(f"taius/{persona_prompt}"))
    template = PromptTemplate(
        input_variables=["user", "idiom", "context", "question"],
        template=prompt.read_prompt(prompt_file.filename, prompt_file.abs_dir))
    final_prompt = template.format(user=username, idiom=idiom, context=response, question=question)
    log.info("FETCH::[QUESTION] '%s'  context: '%s'", question, response)
    llm = lc_llm.create_chat_model(temperature=Temperature.CODE_GENERATION.temp)
    response: AIMessage = llm.invoke(final_prompt)

    if not response or not (output := response.content) or shared.UNCERTAIN_ID in response.content:
        output = msg.translate("Sorry, I was not able to provide a helpful response.")

    return output or msg.translate("Sorry, the query produced no response!")
