from typing import List, Dict

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from askai.core.model.chat_context import ChatContext
from askai.core.support.shared_instances import shared


class LangChainSupport:

    LANG_CHAIN_ROLE_MAP: Dict = {
        "user": HumanMessage,
        "system": SystemMessage,
        "assistant": AIMessage
    }

    def __init__(self):
        pass

    def chat_messages(self, key: str) -> List:
        context: List[ChatContext.ContextEntry] = shared.context[key]
        return [
            self.LANG_CHAIN_ROLE_MAP[c.role](content=c.content) for c in context
        ] or []
