#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.component
      @file: summarizer.py
   @created: Mon, 11 Mar 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.askai_configs import configs
from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.component.cache_service import PERSIST_DIR
from askai.core.model.summary_result import SummaryResult
from askai.core.support.langchain_support import lc_llm
from askai.exception.exceptions import DocumentsNotFound
from functools import lru_cache
from hspylib.core.config.path_object import PathObject
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.text_tools import ensure_endswith, hash_text
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, TextSplitter
from pathlib import Path
from typing import Optional

import logging as log


class Summarizer(metaclass=Singleton):
    """Provide a summarization service to complete queries that require summarization."""

    INSTANCE: "Summarizer"

    @staticmethod
    def extract_result(result: dict) -> tuple[str, str]:
        """Extract the question and answer from the summarization result."""
        question = result["query"] if "query" in result else result["question"]
        answer = result["result"] if "result" in result else result["answer"]
        return question, answer

    def __init__(self):
        self._retriever = None
        self._folder = None
        self._glob = None
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=configs.chunk_size, chunk_overlap=configs.chunk_overlap
        )

    @property
    def persist_dir(self) -> Path:
        summary_hash = hash_text(self.sum_path)
        return Path(f"{PERSIST_DIR}/{summary_hash}")

    @property
    def folder(self) -> str:
        return ensure_endswith(self._folder, "/")

    @folder.setter
    def folder(self, value: str) -> None:
        self._folder = ensure_endswith(value, "/")

    @property
    def glob(self) -> str:
        return self._glob

    @glob.setter
    def glob(self, value: str) -> None:
        self._glob = value

    @property
    def sum_path(self) -> str:
        return f"{self.folder}{self.glob}"

    @property
    def text_splitter(self) -> TextSplitter:
        return self._text_splitter

    @property
    def retriever(self) -> RetrievalQA:
        return self._retriever

    @lru_cache
    def generate(self, folder: str | Path, glob: str) -> bool:
        """Generate a summarization of the folder contents.
        :param folder: The base folder of the summarization.
        :param glob: The glob pattern or file of the summarization.
        """
        self._folder = str(PathObject.of(folder))
        self._glob: str = glob.strip()
        events.reply.emit(message=msg.summarizing(self.sum_path))
        embeddings = lc_llm.create_embeddings()

        try:
            if self.persist_dir.exists():
                log.info("Recovering vector store from: '%s'", self.persist_dir)
                v_store = Chroma(persist_directory=str(self.persist_dir), embedding_function=embeddings)
            else:
                log.info("Summarizing documents from '%s'", self.sum_path)
                documents: list[Document] = DirectoryLoader(self.folder, glob=self.glob).load()
                if len(documents) <= 0:
                    raise DocumentsNotFound(f"Unable to find any document to summarize at: '{self.sum_path}'")
                texts: list[Document] = self._text_splitter.split_documents(documents)
                v_store = Chroma.from_documents(texts, embeddings, persist_directory=str(self.persist_dir))

            self._retriever = RetrievalQA.from_chain_type(
                llm=lc_llm.create_model(), chain_type="stuff", retriever=v_store.as_retriever()
            )
            return True
        except ImportError as err:
            log.error("Unable to summarize '%s' => %s", self.sum_path, err)
            events.reply_error.emit(message=msg.missing_package(err))

        return False

    def exists(self, folder: str | Path, glob: str) -> bool:
        """Return whether or not the summary already exists."""
        summary_hash = hash_text(f"{ensure_endswith(folder, '/')}{glob}")
        return self._retriever is not None and Path(f"{PERSIST_DIR}/{summary_hash}").exists()

    def query(self, *queries: str) -> Optional[list[SummaryResult]]:
        """Answer questions about the summarized content.
        :param queries: The queries to ask the AI engine.
        """
        if queries and self.retriever is not None:
            results: list[SummaryResult] = []
            for query in queries:
                if result := self._invoke(query):
                    results.append(result)
            return results
        return None

    def _invoke(self, query: str) -> Optional[SummaryResult]:
        """Query the AI about a given query based on the summarized content.
        :param query: The query to ask the AI engine.
        """
        if query and (result := self.retriever.invoke({"query": query})):
            return SummaryResult(self._folder, self._glob, *self.extract_result(result))
        return None


assert (summarizer := Summarizer().INSTANCE) is not None
