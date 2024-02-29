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
from dataclasses import dataclass, field
from typing import List

from askai.core.model.terminal_command import TerminalCommand


@dataclass
class QueryResponse:
    """Keep track of the first-query responses."""

    query_type: str = ''
    question: str = ''
    response: str = ''
    terminating: bool = True
    intelligible: bool = False
    require_command: bool = False
    require_internet: bool = False
    require_summarization: bool = False
    commands: List[TerminalCommand] = field(default_factory=list)

