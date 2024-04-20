"""
   @project: HsPyLib-AskAI
   @package: askai.core.support.chat_context
      @file: chat_context.py
   @created: Fri, 28 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""

import os
from collections import defaultdict, namedtuple, deque
from functools import reduce, partial
from typing import Any, Literal, Optional, TypeAlias

from askai.exception.exceptions import TokenLengthExceeded
from hspylib.core.zoned_datetime import now
from langchain_community.chat_message_histories.in_memory import ChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

ChatRoles: TypeAlias = Literal["system", "human", "assistant"]

ContextRaw: TypeAlias = list[dict[str, str]]

LangChainContext: TypeAlias = list[tuple[str, str]]

ContextEntry = namedtuple("ContextEntry", ["created_at", "role", "content"])


class ChatContext:
    """Provide a chat context helper for AI engines."""

    LANGCHAIN_ROLE_MAP: dict = {"human": HumanMessage, "system": SystemMessage, "assistant": AIMessage}

    def __init__(self, token_limit: int, max_context_length: int):
        self._store: dict[Any, deque] = defaultdict(partial(deque, maxlen=max_context_length))
        self._token_limit: int = token_limit * 1024  # The limit is given in KB

    def __str__(self):
        return os.linesep.join(f"'{k}': '{v}'" for k, v in self._store.items())

    def __getitem__(self, key) -> deque[ContextEntry]:
        return self._store[key]

    def push(self, key: str, content: Any, role: ChatRoles = "human") -> ContextRaw:
        """Push a context message to the chat with the provided role."""
        entry = ContextEntry(now(), role, str(content))
        ctx = self._store[key]
        token_length = reduce(lambda total, e: total + len(e.content), ctx, 0) if len(ctx) > 0 else 0
        if (token_length := token_length + len(content)) > self._token_limit:
            raise TokenLengthExceeded(f"Required token length={token_length}  limit={self._token_limit}")
        ctx.append(entry)
        return self.get(key)

    def set(self, key: str, content: Any, role: ChatRoles = "human") -> ContextRaw:
        """Set the context to the chat with the provided role."""
        self.clear(key)
        return self.push(key, content, role)

    def remove(self, key: str, index: int) -> Optional[str]:
        """Remove a context message from the chat at the provided index."""
        val = None
        if ctx := self._store[key]:
            if index < len(ctx):
                val = ctx[index]
                del ctx[index]
        return val

    def get(self, key: str) -> ContextRaw:
        """Retrieve a context from the specified by key."""
        return [{"role": ctx.role, "content": ctx.content} for ctx in self._store[key]] or []

    def join(self, *keys: str) -> LangChainContext:
        """Join contexts specified by keys."""
        context: LangChainContext = []
        token_length = 0
        for key in keys:
            ctx: ContextRaw = self.get(key)
            content: str = os.linesep.join([tk["content"] for tk in ctx])
            token_length += len(content or "")
            if token_length > self._token_limit:
                raise TokenLengthExceeded(f"Required token length={token_length}k  limit={self._token_limit}k")
            if content and ctx not in context:
                list(map(context.append, [(t["role"], t["content"]) for t in ctx]))
        return context

    def flat(self, *keys: str) -> ChatMessageHistory:
        """Flatten contexts specified by keys."""
        history = ChatMessageHistory()
        flatten: LangChainContext = self.join(*keys)
        for ctx_entry in flatten:
            mtype = self.LANGCHAIN_ROLE_MAP[ctx_entry[0]]
            history.add_message(mtype(ctx_entry[1]))
        return history

    def clear(self, *keys: str) -> int:
        """Clear the all the chat context specified by key."""
        for key in keys:
            if self._store[key]:
                del self._store[key]
        return len(self._store)

    def forget(self) -> None:
        """Forget all entries pushed to the chat context."""
        del self._store
        self._store = defaultdict(list)


if __name__ == "__main__":
    c = ChatContext(1000, 5)
    c.push("TESTE", "1 What is the size of the moon?")
    c.push("TESTE", "2 What is the size of the moon?", "assistant")
    c.push("TESTE", "3 Who are you?")
    c.push("TESTE", "4 I'm Taius, you digital assistant", "assistant")
    c.push("TESTE", "5 I'm Taius, you digital assistant", "assistant")
    c.push("TESTE", "6 I'm Taius, you digital assistant", "assistant")
    c.push("TESTE", "7 I'm Taius, you digital assistant", "assistant")
    print(c.flat("TESTE"))
