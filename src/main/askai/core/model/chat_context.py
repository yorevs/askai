"""
   @project: HsPyLib-AskAI
   @package: askai.core.model
      @file: chat_context.py
   @created: Fri, 28 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""

import os
from collections import defaultdict, namedtuple
from functools import reduce
from typing import Any, List, Literal, Optional, TypeAlias

from hspylib.core.zoned_datetime import now

from askai.exception.exceptions import TokenLengthExceeded

ChatRoles: TypeAlias = Literal["system", "human", "assistant"]

ContextRaw: TypeAlias = list[dict[str, str]]

LangChainContext: TypeAlias = list[tuple[str, str]]


class ChatContext:
    """Provide a chat context helper for AI engines."""

    ContextEntry = namedtuple("ContextEntry", ["created_at", "role", "content"], rename=False)

    def __init__(self, token_limit: int):
        self._context = defaultdict(list)
        self._token_limit: int = token_limit * 1024  # The limit is given in KB

    def __str__(self):
        return os.linesep.join(f"'{k}': '{v}'" for k, v in self._context.items())

    def __getitem__(self, key) -> List[ContextEntry]:
        return self._context[key]

    def push(self, key: str, content: Any, role: ChatRoles = "human") -> ContextRaw:
        """Push a context message to the chat with the provided role."""
        entry = ChatContext.ContextEntry(now(), role, str(content))
        ctx = self._context[key]
        token_length = reduce(lambda total, e: total + len(e.content), ctx, 0) if len(ctx) > 0 else 0
        if (token_length := token_length + len(content)) > self._token_limit:
            raise TokenLengthExceeded(f"Required token length={token_length}  limit={self._token_limit}")
        if entry.content not in [c.content for c in ctx]:
            ctx.append(entry)
        return self.get(key)

    def set(self, key: str, content: Any, role: ChatRoles = "human") -> ContextRaw:
        """Set the context to the chat with the provided role."""
        self.clear(key)
        return self.push(key, content, role)

    def remove(self, key: str, index: int) -> Optional[str]:
        """Remove a context message from the chat at the provided index."""
        val = None
        if ctx := self._context[key]:
            if index < len(ctx):
                val = ctx[index]
                del ctx[index]
        return val

    def get(self, key: str) -> ContextRaw:
        """Retrieve a context from the specified by key."""
        return [{"role": ctx.role, "content": ctx.content} for ctx in self._context[key]] or []

    def join(self, *keys: str) -> LangChainContext:
        """Join contexts specified by keys."""
        context: LangChainContext = []
        token_length = 0
        for key in keys:
            ctx: ContextRaw = self.get(key)
            content: str = os.linesep.join([tk['content'] for tk in ctx])
            token_length += len(content or "")
            if token_length > self._token_limit:
                raise TokenLengthExceeded(f"Required token length={token_length}k  limit={self._token_limit}k")
            if content and ctx not in context:
                list(map(context.append, [(t['role'], t['content']) for t in ctx]))
        return context

    def flat(self, *keys: str) -> str:
        """Flatten contexts specified by keys."""
        return os.linesep.join([f"\n{ctx[0].upper()}\n{ctx[1]}" for ctx in self.join(*keys)])

    def clear(self, *keys: str) -> int:
        """Clear the all the chat context specified by key."""
        for key in keys:
            if self._context[key]:
                del self._context[key]
        return len(self._context)

    def forget(self) -> None:
        """Forget all entries pushed to the chat context."""
        del self._context
        self._context = defaultdict(list)


if __name__ == '__main__':
    c = ChatContext(1000)
    c.push("TESTE", 'What is the size of the moon?')
    c.push("TESTE", 'What is the size of the moon?', 'assistant')
    c.push("TESTE", 'Who are you?')
    c.push("TESTE", "I'm Taius, you digital assistant", 'assistant')
    print(c.join("TESTE"))
