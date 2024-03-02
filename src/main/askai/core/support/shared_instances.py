from functools import lru_cache
from typing import Optional, Dict

from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_state

from askai.core.askai_configs import AskAiConfigs
from askai.core.askai_messages import AskAiMessages
from askai.core.askai_prompt import AskAiPrompt
from askai.core.engine.ai_engine import AIEngine
from askai.core.engine.engine_factory import EngineFactory
from askai.core.model.chat_context import ChatContext
from askai.core.processor.ai_processor import AIProcessor


class SharedInstances(metaclass=Singleton):
    """TODO"""

    INSTANCE: 'SharedInstances' = None

    def __init__(self) -> None:
        self._processors: Dict[str, AIProcessor] = {}
        self._engine: Optional[AIEngine] = None
        self._context: Optional[ChatContext] = None
        self._configs: AskAiConfigs = AskAiConfigs()
        self._msg: AskAiMessages = AskAiMessages()
        self._prompt: AskAiPrompt = AskAiPrompt()

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

    @lru_cache
    def find_processor_by_query_type(self, query_type: str) -> Optional['AIProcessor']:
        """TODO"""
        return next((p for p in self._processors.values() if p.supports(query_type)), None)

    @lru_cache
    def find_processor_by_name(self, name: str) -> Optional['AIProcessor']:
        """TODO"""
        return next((p for p in self._processors.values() if type(p).__name__ == name), None)


assert (shared := SharedInstances().INSTANCE) is not None
