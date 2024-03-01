from typing import Optional

from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_state

from askai.core.askai_configs import AskAiConfigs
from askai.core.askai_messages import AskAiMessages
from askai.core.askai_prompt import AskAiPrompt
from askai.core.engine.ai_engine import AIEngine
from askai.core.model.chat_context import ChatContext


class SharedInstances(metaclass=Singleton):
    """TODO"""

    INSTANCE: 'SharedInstances' = None

    def __init__(self) -> None:
        self._engine: Optional[AIEngine] = None
        self._msg: Optional[AskAiMessages] = None
        self._prompt: Optional[AskAiPrompt] = None
        self._context: Optional[ChatContext] = None
        self._configs: Optional[AskAiConfigs] = None

    @property
    def engine(self) -> Optional[AIEngine]:
        return self._engine

    @engine.setter
    def engine(self, value: AIEngine) -> None:
        check_state(self._engine is None, "Once set, this instance is immutable.")
        self._engine = value

    @property
    def msg(self) -> Optional[AskAiMessages]:
        return self._msg

    @msg.setter
    def msg(self, value: AskAiMessages) -> None:
        check_state(self._msg is None, "Once set, this instance is immutable.")
        self._msg = value

    @property
    def prompt(self) -> Optional[AskAiPrompt]:
        return self._prompt

    @prompt.setter
    def prompt(self, value: AskAiPrompt) -> None:
        check_state(self._prompt is None, "Once set, this instance is immutable.")
        self._prompt = value

    @property
    def context(self) -> Optional[ChatContext]:
        return self._context

    @context.setter
    def context(self, value: ChatContext) -> None:
        check_state(self._context is None, "Once set, this instance is immutable.")
        self._context = value

    @property
    def configs(self) -> Optional[AskAiConfigs]:
        return self._configs

    @configs.setter
    def configs(self, value: AskAiConfigs) -> None:
        check_state(self._configs is None, "Once set, this instance is immutable.")
        self._configs = value


assert SharedInstances().INSTANCE is not None
