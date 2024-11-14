#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: taius-coder
   @package: askai.core.processors.chat
      @file: chat.py
   @created: Mon, 23 Sep 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/taius-coder
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright 2024, HSPyLib team
"""
from typing import Any, Optional

from clitt.core.term.cursor import cursor
from hspylib.core.config.path_object import PathObject
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.dict_tools import get_or_default_by_key
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory
from rich.live import Live
from rich.spinner import Spinner

from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperature import Temperature
from askai.core.model.ai_reply import AIReply
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter as tf
from askai.exception.exceptions import TerminatingQuery


class ChatProcessor(metaclass=Singleton):
    """TODO"""

    INSTANCE: "ChatProcessor"

    def template(self, prompt_str: str, *inputs: str, **kwargs) -> ChatPromptTemplate:
        """Retrieve the processor Template."""

        template = PromptTemplate(input_variables=list(inputs), template=prompt_str)

        # fmt: off
        return ChatPromptTemplate.from_messages([
            ("system", template.format(**kwargs)),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        # fmt: on

    def process(self, question: str, **kwargs) -> Optional[str]:
        """Process the user question to retrieve the final response.
        :param question: The user question to process.
        :return: The final response after processing the question.
        """

        if not question:
            raise TerminatingQuery("The user wants to exit!")
        if question.casefold() in ["exit", "leave", "quit", "q"]:
            events.reply.emit(reply=AIReply.info(msg.leave_chat()))
            events.mode_changed.emit(mode="DEFAULT")
            return None

        with Live(
            Spinner("dots", f"[green]{msg.wait()}[/green]", style="green"), console=tf.console
        ):
            response = None
            prompt_file: str = get_or_default_by_key(kwargs, "prompt_file", None)
            history_ctx: Any | None = get_or_default_by_key(kwargs, "history_ctx", "HISTORY")
            ctx: str = get_or_default_by_key(kwargs, "context", "")
            inputs: list[str] = get_or_default_by_key(kwargs, "inputs", [])
            args: dict[str, Any] = get_or_default_by_key(kwargs, "args", {})
            inputs = inputs or ["user", "idiom", "context", "question"]
            args = args or {"user": prompt.user.title(), "idiom": shared.idiom, "context": ctx, "question": question}
            prompt_file: PathObject = PathObject.of(prompt_file or prompt.append_path(f"taius/taius-jarvis"))
            prompt_str: str = prompt.read_prompt(prompt_file.filename, prompt_file.abs_dir)

            template = self.template(prompt_str, *inputs, **args)
            runnable = template | lc_llm.create_chat_model(Temperature.COLDEST.temp)
            runnable = RunnableWithMessageHistory(
                runnable, shared.context.flat, input_messages_key="input", history_messages_key="chat_history"
            )

            if output := runnable.invoke(
                input={"input": question},
                config={"configurable": {"session_id": history_ctx or ""}}):
                response = output.content

        cursor.erase_line()

        return response


assert (chat := ChatProcessor().INSTANCE) is not None
