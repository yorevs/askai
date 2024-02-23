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
from typing import List

from askai.core.model.query_type import QueryType


@dataclass
class QueryResponse:
    """Keep track of the query responses."""

    query_type: QueryType
    question: str
    require_internet: bool
    commands: List[dict]
    summarization: List[dict]
    uploads: List[dict]
    downloads: List[dict]


