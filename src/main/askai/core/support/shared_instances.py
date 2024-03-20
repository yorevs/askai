from typing import Optional

from clitt.core.term.terminal import terminal
from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_state
from hspylib.modules.cli.keyboard import Keyboard

from askai.core.askai_prompt import prompt
from askai.core.engine.ai_engine import AIEngine
from askai.core.engine.engine_factory import EngineFactory
from askai.core.model.chat_context import ChatContext
from askai.core.support.utilities import display_text


class SharedInstances(metaclass=Singleton):
    """TODO"""

    INSTANCE: "SharedInstances" = None

    def __init__(self) -> None:
        self._engine: Optional[AIEngine] = None
        self._context: Optional[ChatContext] = None

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
        return f"  {self.engine.nickname()}"

    @property
    def username(self) -> str:
        return f"  {prompt.user.title()}"

    def create_engine(self, engine_name: str, model_name: str) -> AIEngine:
        """TODO"""
        if self._engine is None:
            self._engine = EngineFactory.create_engine(engine_name, model_name)
        return self._engine

    def create_context(self, token_limit: int) -> ChatContext:
        """TODO"""
        if self._context is None:
            self._context = ChatContext(token_limit)
        return self._context

    def input_text(self, input_prompt: str) -> Optional[str]:
        """Prompt for user input.
        :param input_prompt: The prompt to display to the user.
        """
        ret = None
        while ret is None:
            if (ret := line_input(input_prompt)) == Keyboard.VK_CTRL_L:  # Use STT as input method.
                terminal.cursor.erase_line()
                if spoken_text := self.engine.speech_to_text():
                    display_text(f"{self.username}: {spoken_text}")
                    ret = spoken_text

        return ret if not ret or isinstance(ret, str) else ret.val


assert (shared := SharedInstances().INSTANCE) is not None
