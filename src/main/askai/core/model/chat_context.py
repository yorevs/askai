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
from typing import Any, Literal, Optional, List, TypeAlias

from hspylib.core.zoned_datetime import now

from askai.exception.exceptions import TokenLengthExceeded

ChatRoles: TypeAlias = Literal['system', 'user', 'assistant']


class ChatContext:
    """Provide a chat context helper for AI engines."""

    ContextEntry = namedtuple('ContextEntry', ['created_at', 'role', 'content'], rename=False)

    def __init__(self, token_limit: int):
        self._context = defaultdict(list)
        self._token_limit: int = token_limit * 1024  # The limit is given in KB

    def __str__(self):
        return os.linesep.join(f"'{k}': '{v}'" for k, v in self._context.items())

    def __getitem__(self, key) -> List[ContextEntry]:
        return self._context[key]

    def push(self, key: str, content: Any, role: ChatRoles = 'user') -> List[dict]:
        """Push a context message to the chat with the provided role."""
        entry = ChatContext.ContextEntry(now(), role, str(content))
        ctx = self._context[key]
        token_length = reduce(lambda total, e: total + len(e.content), ctx, 0) if len(ctx) > 0 else 0
        if (token_length := token_length + len(content)) > self._token_limit:
            raise TokenLengthExceeded(f"Required token length={token_length}  limit={self._token_limit}")
        ctx.append(entry)
        return self.get(key)

    def set(self, key: str, content: Any, role: ChatRoles = 'user') -> List[dict]:
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

    def get(self, key: str) -> List[dict]:
        """Retrieve a context from the specified by key."""
        return [
            {'role': c.role, 'content': c.content} for c in self._context[key]
        ] or []

    def get_many(self, *keys: str) -> List[dict]:
        """Retrieve many contexts from the specified by key."""
        context = []
        for key in keys:
            context += self.get(key)
        return context

    def clear(self, key: str) -> int:
        """Clear the all the chat context specified by key."""
        if self._context[key]:
            del self._context[key]
        return len(self._context)
