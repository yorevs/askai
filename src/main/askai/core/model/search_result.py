from dataclasses import dataclass
from typing import List

import json


@dataclass
class SearchResult:
    """Keep track of the internet search responses."""

    keywords: List[str] = None
    urls: str | List[str] = None
    results: str = None

    def __str__(self):
        return f"Internet search results: {json.dumps(self.__dict__, default=lambda obj: obj.__dict__)}"
