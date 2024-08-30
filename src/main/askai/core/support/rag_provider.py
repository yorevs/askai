#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.support
      @file: rag_provider.py
   @created: Wed, 28 Aug 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.__classpath__ import classpath
from askai.core.support.langchain_support import lc_llm
from functools import lru_cache
from hspylib.core.preconditions import check_state
from hspylib.core.tools.commons import file_is_not_empty
from langchain_community.document_loaders import CSVLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from pathlib import Path

import os


class RAGProvider:
    """A class responsible for implementing the Retrieval-Augmented Generation (RAG) mechanism."""

    RAG_DIR: Path = Path(os.path.join(classpath.resource_path(), "assets/rag"))

    def __init__(self, rag_filepath: str):
        self._rag_db = None
        self._rag_path: str = os.path.join(str(self.RAG_DIR), rag_filepath)
        self._rag_docs: list[Document] = CSVLoader(file_path=self._rag_path).load()
        self._rag_db: VectorStore | None = None
        check_state(file_is_not_empty(self._rag_path))

    @lru_cache
    def retrieve_examples(self, query: str, k: int = 3) -> list[str]:
        """Retrieve a list of relevant examples based on the provided query.
        :param query: The search query used to retrieve examples.
        :param k: The number of examples to retrieve (default is 3).
        :return: A list of strings representing the retrieved examples.
        """
        if self._rag_db is None:
            self._rag_db = FAISS.from_documents(self._rag_docs, lc_llm.create_embeddings())
        example_docs: list[Document] = self._rag_db.similarity_search(query, k=k)
        return [doc.page_content for doc in example_docs]
