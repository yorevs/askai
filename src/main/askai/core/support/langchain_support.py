"""
   @project: HsPyLib-AskAI
   @package: askai.core.support.langchain_support
      @file: langchain_support.py
   @created: Fri, 28 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

from askai.core.support.shared_instances import shared
from functools import lru_cache
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_not_none
from langchain_core.documents import Document
from typing import Any, List, Type


def load_document(loader_type: Type, url: str | List[str]) -> List[Document]:
    """TODO"""
    return loader_type(url).load()


class LangChainSupport(metaclass=Singleton):
    """TODO"""

    INSTANCE: ""

    @staticmethod
    @lru_cache
    def create_model(temperature: float = 0.0, top_p: float = 0.0) -> Any:
        """TODO"""
        check_not_none(shared.engine, "AI Engine was not created yet!")
        return shared.engine.lc_model(temperature, top_p)

    @staticmethod
    @lru_cache
    def create_chat_model(temperature: float = 0.0) -> Any:
        """TODO"""
        check_not_none(shared.engine, "AI Engine was not created yet!")
        return shared.engine.lc_chat_model(temperature)

    @staticmethod
    @lru_cache
    def create_embeddings() -> Any:
        """TODO"""
        check_not_none(shared.engine, "AI Engine was not created yet!")
        return shared.engine.lc_embeddings()


assert (lc_llm := LangChainSupport().INSTANCE) is not None
