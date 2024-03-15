from askai.core.model.chat_context import ChatContext
from askai.core.support.shared_instances import shared
from functools import lru_cache
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_not_none
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import Any, Dict, List, Type


def load_document(loader_type: Type, url: str | List[str]) -> List[Document]:
    """TODO"""
    return loader_type(url).load()


class LangChainSupport(metaclass=Singleton):
    """TODO"""

    INSTANCE: "" = None

    LANGCHAIN_ROLE_MAP: Dict = {"user": HumanMessage, "system": SystemMessage, "assistant": AIMessage}

    @staticmethod
    @lru_cache
    def create_model(temperature: float = 0.0, top_p: float = 0.0) -> Any:
        """TODO"""
        check_not_none(shared.engine, "AI Engine was not created yet!")
        return shared.engine.lc_model(temperature, top_p)

    @staticmethod
    @lru_cache
    def create_chat_model(temperature: float = 0.0) -> Any:
        """TODO"""
        check_not_none(shared.engine, "AI Engine was not created yet!")
        return shared.engine.lc_chat_model(temperature)

    @staticmethod
    @lru_cache
    def create_embeddings() -> Any:
        """TODO"""
        check_not_none(shared.engine, "AI Engine was not created yet!")
        return shared.engine.lc_embeddings()

    @classmethod
    @lru_cache
    def get_context(cls, key: str) -> List:
        """TODO"""
        context: List[ChatContext.ContextEntry] = shared.context[key]
        return [cls.LANGCHAIN_ROLE_MAP[c.role](content=c.content) for c in context] or []


assert (lc_llm := LangChainSupport().INSTANCE) is not None
