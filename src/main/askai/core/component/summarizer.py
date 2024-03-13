#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.component
      @file: summarizer.py
   @created: Mon, 11 Mar 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
import logging as log
import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

import nltk
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_argument
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.model.summary_result import SummaryResult
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared


class Summarizer(metaclass=Singleton):
    """Provide a summarization service to complete queries that require summarization."""

    INSTANCE: "Summarizer" = None

    ASKAI_SUMMARY_DATA_KEY = "askai-summary-data"

    def __init__(self):
        nltk.download('averaged_perceptron_tagger')
        self._retriever = None
        self._path = None
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=0, separators=[" ", ", ", "\n"])

    def generate(self, path: str | Path, glob: str = None) -> None:
        """TODO"""
        self._path = f"{path}/{glob}"
        path = path.replace("~", os.getenv("HOME")).strip()
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.summarizing(self._path))
        log.info("Summarizing documents: '%s'/'%s'", path, glob)
        loader = DirectoryLoader(str(path), glob=glob)
        documents: List[Document] = loader.load()
        texts: List[Document] = self._text_splitter.split_documents(documents)
        embeddings = lc_llm.create_embeddings()
        doc_store = Chroma.from_documents(texts, embeddings)
        self._retriever = RetrievalQA.from_chain_type(
            llm=lc_llm.create_model(), chain_type="stuff", retriever=doc_store.as_retriever())

    def query(self, *queries: str) -> Optional[List[SummaryResult]]:
        """TODO"""
        check_argument(len(queries) > 0)
        if self._retriever is not None:
            results: List[SummaryResult] = []
            for query_string in queries:
                if result := self.query_one(query_string):
                    results.append(result)
            return results
        return None

    @lru_cache
    def query_one(self, query_string: str) -> Optional[SummaryResult]:
        """TODO"""
        check_argument(len(query_string) > 0)
        if result := self._retriever.invoke({"query": query_string}):
            return SummaryResult(self._path, result['query'].strip(), result['result'].strip())
        return None


assert (summarizer := Summarizer().INSTANCE) is not None


if __name__ == '__main__':
    shared.create_engine('openai', 'gpt-3.5-turbo')
    summarizer.generate("/Users/hjunior/HomeSetup/docs", "**/*.md")
    print(summarizer.query(
        "What is HomeSetup?",
        "How can I install HomeSetup?",
        "How can I configure my Starship prompt?",
        "How can change the starship preset?"))
