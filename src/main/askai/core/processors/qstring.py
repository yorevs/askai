#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.processors.qstring
      @file: qstring.py
   @created: Fri, 5 May 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from clitt.core.term.cursor import cursor
from rich.live import Live
from rich.spinner import Spinner

from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import cache
from askai.core.engine.openai.temperature import Temperature
from askai.core.support.langchain_support import lc_llm
from askai.core.support.utilities import find_file
from askai.core.support.text_formatter import text_formatter as tf
from askai.exception.exceptions import TerminatingQuery
from hspylib.core.config.path_object import PathObject
from hspylib.core.metaclass.singleton import Singleton
from langchain_core.prompts import PromptTemplate
from typing import Optional


class NonInteractive(metaclass=Singleton):
    """Processor to provide a answers from custom prompts (non-interactive)."""

    INSTANCE: "NonInteractive"

    DEFAULT_PROMPT: str = f"{prompt.PROMPT_DIR}/taius/taius-non-interactive"

    DEFAULT_CONTEXT: str = "No context has been provided"

    DEFAULT_TEMPERATURE: int = Temperature.CREATIVE_WRITING.temp

    def process(self, question: str, **kwargs) -> Optional[str]:
        """Process the user question to retrieve the final response.
        :param question: The user question to process.
        """

        if not question:
            raise TerminatingQuery("The user wants to exit!")
        if question.casefold() in ["exit", "leave", "quit", "q"]:
            return None

        with Live(
            Spinner("dots", f"[green]{msg.wait()}[/green]", style="green"), console=tf.console
        ):
            output = None
            query_prompt: str | None = find_file(kwargs["query_prompt"]) if "query_prompt" in kwargs else None
            context: str | None = kwargs["context"] if "context" in kwargs else None
            temperature: int = kwargs["temperature"] if "temperature" in kwargs else None

            dir_name, file_name = PathObject.split(query_prompt or self.DEFAULT_PROMPT)
            template = PromptTemplate(
                input_variables=["context", "question"], template=prompt.read_prompt(file_name, dir_name)
            )
            final_prompt: str = template.format(context=context or self.DEFAULT_CONTEXT, question=question)
            llm = lc_llm.create_chat_model(temperature or self.DEFAULT_TEMPERATURE)

            if (response := llm.invoke(final_prompt)) and (output := response.content):
                cache.save_input_history()

        cursor.erase_line()

        return output


assert (qstring := NonInteractive().INSTANCE) is not None
