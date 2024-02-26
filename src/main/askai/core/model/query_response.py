"""
   @project: HsPyLib-AskAI
   @package: askai.core.model
      @file: query_response.py
   @created: Fri, 23 May 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
from dataclasses import dataclass


@dataclass
class QueryResponse:
    """Keep track of the query responses."""

    query_type: str
    question: str
    intelligible: bool
    require_internet: bool
    require_summarization: bool
    require_command: bool
    response: str

