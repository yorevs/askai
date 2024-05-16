#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: "askai"
   @package: "askai".main.askai.core.support
      @file: shared_instances.py
   @created: Tue, 23 Apr 2024
    @author: "<B>H</B>ugo <B>S</B>aporetti <B>J</B>unior")"
      @site: "https://github.com/yorevs/askai")
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

from askai.core.askai_configs import configs
from askai.core.askai_prompt import prompt
from askai.core.engine.ai_engine import AIEngine
from askai.core.engine.engine_factory import EngineFactory
from askai.core.support.chat_context import ChatContext
from askai.core.support.utilities import display_text
from clitt.core.term.terminal import terminal
from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_state
from hspylib.modules.cli.keyboard import Keyboard
from langchain.memory import ConversationBufferWindowMemory
from typing import Optional


class SharedInstances(metaclass=Singleton):
    """Provides access to shared instances."""

    INSTANCE: "SharedInstances"

    # This is the uuid used in the prompts to indicate that the AI does not know the answer.
    UNCERTAIN_ID: str = "bde6f44d-c1a0-4b0c-bd74-8278e468e50c"

    def __init__(self) -> None:
        self._engine: AIEngine | None = None
        self._context: ChatContext | None = None
        self._memory: ConversationBufferWindowMemory | None = None
        self._idiom: str = configs.language.idiom
        self._max_short_memory_size: int = configs.max_short_memory_size
        self._max_iteractions: int = configs.max_iteractions

    @property
    def engine(self) -> Optional[AIEngine]:
        return self._engine

    @engine.setter
    def engine(self, value: AIEngine) -> None:
        check_state(self._engine is None, "Once set, this instance is immutable.")
        self._engine = value

    @property
    def context(self) -> Optional[ChatContext]:
        return self._context

    @context.setter
    def context(self, value: ChatContext) -> None:
        check_state(self._context is None, "Once set, this instance is immutable.")
        self._context = value

    @property
    def nickname(self) -> str:
        return f"%GREEN%  Taius%NC%"

    @property
    def username(self) -> str:
        return f"%WHITE%  {prompt.user.title()}%NC%"

    @property
    def idiom(self) -> str:
        return self._idiom

    @property
    def memory(self) -> ConversationBufferWindowMemory:
        return self.create_memory()

    @property
    def max_short_memory_size(self) -> int:
        return self._max_short_memory_size

    @property
    def max_iteractions(self) -> int:
        return self._max_iteractions

    def create_engine(self, engine_name: str, model_name: str) -> AIEngine:
        """TODO"""
        if self._engine is None:
            self._engine = EngineFactory.create_engine(engine_name, model_name)
        return self._engine

    def create_context(self, token_limit: int) -> ChatContext:
        """TODO"""
        if self._context is None:
            self._context = ChatContext(token_limit, self.max_short_memory_size)
        return self._context

    def create_memory(self, memory_key: str = "chat_history") -> ConversationBufferWindowMemory:
        """TODO"""
        if self._memory is None:
            self._memory = ConversationBufferWindowMemory(
                memory_key=memory_key, k=configs.max_short_memory_size, return_messages=True
            )
        return self._memory

    def input_text(self, input_prompt: str, placeholder: str | None = None) -> Optional[str]:
        """Prompt for user input.
        :param input_prompt: The prompt to display to the user.
        :param placeholder: The input placeholder text.
        """
        ret = None
        while ret is None:
            if (ret := line_input(input_prompt, placeholder)) == Keyboard.VK_CTRL_L:  # Use STT as input method.
                terminal.cursor.erase_line()
                if spoken_text := self.engine.speech_to_text():
                    display_text(f"{self.username}: {spoken_text}")
                    ret = spoken_text

        return ret if not ret or isinstance(ret, str) else ret.val


assert (shared := SharedInstances().INSTANCE) is not None
