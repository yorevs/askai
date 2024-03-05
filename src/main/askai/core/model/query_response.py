"""
   @project: HsPyLib-AskAI
   @package: askai.core.model
      @file: query_response.py
   @created: Fri, 23 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
import json
from dataclasses import dataclass, field
from typing import List

from askai.core.model.terminal_command import TerminalCommand


@dataclass
class QueryResponse:
    """Keep track of the first-query responses."""

    query_type: str = ''
    question: str = ''
    response: str = ''
    terminating: bool = False
    intelligible: bool = True
    require_command: bool = False
    require_internet: bool = False
    require_summarization: bool = False
    commands: List[TerminalCommand] = field(default_factory=list)

    @staticmethod
    def of_string(question: str, plain_response: str) -> '':
        """Sometimes AI gets cray and don't return a JSON string, so we have to fix it."""
        return QueryResponse(
            'GenericProcessor', question, plain_response,
            False, True, False, False, False
        )

    def __str__(self):
        return json.dumps(self.__dict__, default=lambda obj: obj.__dict__)
