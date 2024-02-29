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
from typing import Any, Literal, Optional, List

from askai.exception.exceptions import TokenLengthExceeded


class ChatContext:
    """TODO"""

    ContextEntry = namedtuple('ContextEntry', ['role', 'content'], rename=False)

    def __init__(self, token_limit: int):
        self._context = defaultdict(list)
        self._token_limit: int = token_limit

    def __str__(self):
        return os.linesep.join(f"'{k}': '{v}'" for k, v in self._context.items())

    def __getitem__(self, key) -> List[ContextEntry]:
        return self._context[key]

    def push(self, key: str, content: Any, role: Literal['system', 'user', 'assistant'] = 'user') -> List[dict]:
        """TODO"""
        entry = ChatContext.ContextEntry(role, str(content))
        ctx = self._context[key]
        token_length = reduce(lambda total, e: total + len(e.content), ctx, 0) if len(ctx) > 0 else 0
        if (token_length := token_length + len(content)) > self._token_limit:
            raise TokenLengthExceeded(f"Required token length={token_length}  limit={self._token_limit}")
        ctx.append(entry)
        return self.get(key)

    def remove(self, key: str, index: int) -> Optional[str]:
        """TODO"""
        val = None
        if ctx := self._context[key]:
            if index < len(ctx):
                val = ctx[index]
                del ctx[index]
        return val

    def get(self, key: str) -> List[dict]:
        """TODO"""
        return [{'role': c.role, 'content': c.content} for c in self._context[key]] or []

    def clear(self, key: str) -> int:
        """TODO"""
        if self._context[key]:
            del self._context[key]
        return len(self._context)


if __name__ == '__main__':
    cc = ChatContext(100)
    cc.push('TYPE-1', 'This is a type 1 query', 'system')
    cc.push('TYPE-2', 'This is a type 2 query', 'system')
    cc.push('TYPE-2', 'List my downloads')
    cc.push('TYPE-1', 'What is the size of the moon')
    cc.push('TYPE-1', '*' * 50)
    print(cc)
    print('CTX-1', cc.get('TYPE-1'))
    print('CTX-2', cc.get('TYPE-2'))
    print('CTX-3', cc.get('TYPE-3'))
    print('TYPE-1.1', cc['TYPE-1'][0])
    print('TYPE-1.2', cc['TYPE-1'][1])
    print('TYPE-1.3', cc['TYPE-1'][2])
