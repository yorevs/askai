"""
   @project: HsPyLib-AskAI
   @package: askai.core.model
      @file: processor_response.py
   @created: Fri, 23 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""

from askai.core.model.terminal_command import TerminalCommand
from dataclasses import dataclass, field
from typing import List

import json


@dataclass
class ProcessorResponse:
    """Keep track of the processor responses."""

    query_type: str = ""
    question: str = ""
    response: str = ""
    terminating: bool = False
    intelligible: bool = False
    forwarded: bool = False
    require_summarization: bool = False
    commands: List[TerminalCommand] = field(default_factory=list)

    def __str__(self):
        return json.dumps(self.__dict__, default=lambda obj: obj.__dict__)
