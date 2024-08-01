#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.support.chat_context
      @file: chat_context.py
   @created: Fri, 28 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import re

from askai.core.component.cache_service import cache
from askai.exception.exceptions import TokenLengthExceeded
from collections import defaultdict, deque, namedtuple
from functools import partial, reduce
from langchain_community.chat_message_histories.in_memory import ChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import Any, AnyStr, Literal, Optional, TypeAlias

import os

ChatRoles: TypeAlias = Literal["system", "human", "assistant"]

ContextRaw: TypeAlias = list[dict[str, str]]

LangChainContext: TypeAlias = list[tuple[str, str]]

ContextEntry = namedtuple("ContextEntry", ["role", "content"])


class ChatContext:
    """Provide a chat context helper for AI engines."""

    LANGCHAIN_ROLE_MAP: dict = {"human": HumanMessage, "system": SystemMessage, "assistant": AIMessage}

    @staticmethod
    def of(context: list[str], token_limit: int, max_context_size: int) -> 'ChatContext':
        """Create a chat context from a context list on the format: <ROLE: MSG>"""
        ctx = ChatContext(token_limit, max_context_size)
        for e in context:
            role, reply = list(filter(None, re.split(r'(human|assistant|system):', e, flags=re.MULTILINE | re.IGNORECASE)))
            ctx.push("HISTORY", reply, role)
        return ctx

    def __init__(self, token_limit: int, max_context_size: int):
        self._store: dict[AnyStr, deque] = defaultdict(partial(deque, maxlen=max_context_size))
        self._token_limit: int = token_limit * 1024  # The limit is given in KB
        self._max_context_size: int = max_context_size

    def __str__(self):
        ln: str = os.linesep
        return ln.join(f"'{k}': '{v}'" + ln for k, v in self._store.items())

    def __getitem__(self, key) -> deque[ContextEntry]:
        return self._store[key]

    def __iter__(self):
        return zip(self._store.keys().__iter__(), self._store.values().__iter__())

    def __len__(self):
        return self._store.__len__()

    @property
    def keys(self) -> list[AnyStr]:
        return [str(k) for k in self._store.keys()]

    @property
    def max_context_size(self) -> int:
        return self._max_context_size

    @property
    def token_limit(self) -> int:
        return self._token_limit

    def push(self, key: str, content: Any, role: ChatRoles = "human") -> ContextRaw:
        """Push a context message to the chat with the provided role."""
        entry = ContextEntry(role, str(content))
        ctx = self._store[key]
        if (token_length := (self.context_length(key)) + len(content)) > self._token_limit:
            raise TokenLengthExceeded(f"Required token length={token_length}  limit={self._token_limit}")
        if entry not in ctx:
            ctx.append(entry)
        return self.get(key)

    def context_length(self, key: str):
        ctx = self._store[key]
        return reduce(lambda total, e: total + len(e.content), ctx, 0) if len(ctx) > 0 else 0

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
        count = 0
        contexts = list(keys or self._store.keys())
        while contexts and (key := contexts.pop()):
            if key in self._store:
                del self._store[key]
                count += 1
        return count

    def forget(self, *keys: str) -> None:
        """Forget all entries pushed to the chat context."""
        self.clear(*keys)

    def size(self, key: str) -> int:
        """Return the amount of entries a context specified by key have."""
        return len(self._store[key])

    def save(self) -> None:
        """Save the current context window."""
        ctx: LangChainContext = self.join(*self._store.keys())
        ctx_str: list[str] = [f"{role}: {msg}" for role, msg in ctx]
        cache.save_context(ctx_str)
