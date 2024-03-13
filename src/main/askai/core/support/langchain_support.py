from typing import Any, Dict, List

from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_not_none
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from askai.core.model.chat_context import ChatContext
from askai.core.support.shared_instances import shared


class LangChainSupport(metaclass=Singleton):
    """TODO"""

    INSTANCE: "" = None

    LANGCHAIN_ROLE_MAP: Dict = {"user": HumanMessage, "system": SystemMessage, "assistant": AIMessage}

    @staticmethod
    def create_model(temperature: float = 0.8, top_p: float = 0.0) -> Any:
        """TODO"""
        check_not_none(shared.engine, "AI Engine was not created yet!")
        return shared.engine.lc_model(temperature, top_p)

    @staticmethod
    def create_embeddings() -> Any:
        """TODO"""
        check_not_none(shared.engine, "AI Engine was not created yet!")
        return shared.engine.lc_embeddings()

    @classmethod
    def get_context(cls, key: str) -> List:
        """TODO"""
        context: List[ChatContext.ContextEntry] = shared.context[key]
        return [cls.LANGCHAIN_ROLE_MAP[c.role](content=c.content) for c in context] or []


assert (lc_llm := LangChainSupport().INSTANCE) is not None
