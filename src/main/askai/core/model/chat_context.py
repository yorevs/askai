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

from askai.exception.exceptions import TokenLengthExceeded
from collections import defaultdict, namedtuple
from functools import reduce
from hspylib.core.zoned_datetime import now
from typing import Any, Dict, List, Literal, Optional, TypeAlias

import os

ChatRoles: TypeAlias = Literal["system", "user", "assistant"]

ContextRaw: TypeAlias = List[Dict[str, str]]


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

    def push(self, key: str, content: Any, role: ChatRoles = "user") -> ContextRaw:
        """Push a context message to the chat with the provided role."""
        entry = ChatContext.ContextEntry(now(), role, str(content))
        ctx = self._context[key]
        token_length = reduce(lambda total, e: total + len(e.content), ctx, 0) if len(ctx) > 0 else 0
        if (token_length := token_length + len(content)) > self._token_limit:
            raise TokenLengthExceeded(f"Required token length={token_length}  limit={self._token_limit}")
        if entry.content not in [c.content for c in ctx]:
            ctx.append(entry)
        return self.get(key)

    def set(self, key: str, content: Any, role: ChatRoles = "user") -> ContextRaw:
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
        return [{"role": c.role, "content": c.content} for c in self._context[key]] or []

    def join(self, *keys: str) -> ContextRaw:
        """Join contexts specified by keys."""
        context: ContextRaw = []
        token_length = 0
        for key in keys:
            ctx = self.get(key)
            content = " ".join([t["content"] for t in ctx])
            token_length += len(content or "")
            if token_length > self._token_limit:
                raise TokenLengthExceeded(f"Required token length={token_length}k  limit={self._token_limit}k")
            if content and ctx not in context:
                context.extend(ctx)
        return context

    def flat(self, *keys: str) -> str:
        """Flatten contexts specified by keys."""
        return os.linesep.join([ctx["content"] for ctx in self.join(*keys)])

    def clear(self, *keys: str) -> int:
        """Clear the all the chat context specified by key."""
        for key in keys:
            if self._context[key]:
                del self._context[key]
        return len(self._context)
