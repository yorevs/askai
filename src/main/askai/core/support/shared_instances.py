from functools import lru_cache
from typing import Optional, Any

from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_state, check_not_none

from askai.core.engine.ai_engine import AIEngine
from askai.core.engine.engine_factory import EngineFactory
from askai.core.model.chat_context import ChatContext


class SharedInstances(metaclass=Singleton):
    """TODO"""

    INSTANCE: 'SharedInstances' = None

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
    def create_langchain_model(self, **kwargs) -> Any:
        """TODO"""
        check_not_none(self._engine, "AI Engine was not created yet!")
        return self.engine.lc_model(**kwargs)


assert (shared := SharedInstances().INSTANCE) is not None
