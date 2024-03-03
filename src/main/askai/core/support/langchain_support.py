from functools import lru_cache
from typing import List, Dict, Any

from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_not_none
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from askai.core.model.chat_context import ChatContext
from askai.core.support.shared_instances import shared


class LangChainSupport(metaclass=Singleton):

    INSTANCE: '' = None

    LANGCHAIN_ROLE_MAP: Dict = {
        "user": HumanMessage,
        "system": SystemMessage,
        "assistant": AIMessage
    }

    def get_context(self, key: str) -> List:
        """TODO"""
        context: List[ChatContext.ContextEntry] = shared.context[key]
        return [
            self.LANGCHAIN_ROLE_MAP[c.role](content=c.content) for c in context
        ] or []

    @lru_cache
    def create_langchain_model(self, **kwargs) -> Any:
        """TODO"""
        check_not_none(shared.engine, "AI Engine was not created yet!")
        return shared.engine.lc_model(**kwargs)


assert (lc_llm := LangChainSupport().INSTANCE) is not None
