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
from askai.core.model.ai_reply import AIReply
from askai.core.model.summary_result import SummaryResult
from askai.core.support.langchain_support import lc_llm
from askai.exception.exceptions import DocumentsNotFound
from functools import lru_cache
from hspylib.core.config.path_object import PathObject
from hspylib.core.metaclass.classpath import AnyPath
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.text_tools import ensure_endswith, hash_text
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter, TextSplitter
from pathlib import Path
from rich.status import Status
from typing import Optional

import logging as log


class Summarizer(metaclass=Singleton):
    """Provide a summarization service to complete queries that require summarization. This class is designed to
    generate concise summaries of text data, which can be used to condense lengthy content into more digestible
    information. It leverages natural language processing techniques to extract key points and present them in a
    coherent manner.
    """

    INSTANCE: "Summarizer"

    @staticmethod
    def extract_result(result: dict) -> tuple[str, str]:
        """Extract the question and answer from the summarization result.
        :param result: A dictionary containing the summarization result.
        :return: A tuple containing the question and the answer.
        """
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
    def generate(self, folder: AnyPath, glob: str) -> bool:
        """Generate a summarization of the contents within a specified folder. This method analyzes files within the
        given folder that match the provided glob pattern and creates a summarization of their contents.
        :param folder: The base folder where files are located.
        :param glob: The glob pattern or specific file name used to filter the files for summarization.
        :return: A boolean indicating the success or failure of the summarization process.
        """
        self._folder: str = str(PathObject.of(folder))
        self._glob: str = glob.strip()
        events.reply.emit(reply=AIReply.info(msg.summarizing(self.sum_path)))
        embeddings: Embeddings = lc_llm.create_embeddings()
        v_store: Chroma | None = None

        try:
            if self.persist_dir.exists():
                log.info("Recovering vector store from: '%s'", self.persist_dir)
                v_store = Chroma(persist_directory=str(self.persist_dir), embedding_function=embeddings)
            else:
                log.info("Summarizing documents from '%s'", self.sum_path)
                with Status(f"[green]{msg.summarizing(self.folder)}[/green]"):
                    documents: list[Document] = DirectoryLoader(self.folder, glob=self.glob).load()
                    if len(documents) <= 0:
                        raise DocumentsNotFound(f"Unable to find any document to summarize at: '{self.sum_path}'")
                    texts: list[Document] = self._text_splitter.split_documents(documents)
                    v_store = Chroma.from_documents(texts, embeddings, persist_directory=str(self.persist_dir))

            self._retriever = RetrievalQA.from_chain_type(
                llm=lc_llm.create_chat_model(), chain_type="stuff", retriever=v_store.as_retriever()
            )
            return True
        except ImportError as err:
            log.error("Unable to summarize '%s' => %s", self.sum_path, err)
            events.reply.emit(reply=AIReply.error(msg.missing_package(err)))

        return False

    @lru_cache
    def exists(self, folder: AnyPath, glob: str) -> bool:
        """Check if a summarization exists for the specified folder and glob pattern. This method determines whether a
        summarization has been created for the contents of the given folder that match the provided glob pattern.
        :param folder: The base folder where files are located.
        :param glob: The glob pattern or file name used to filter the files for which the summarization was created.
        :return: True if a summarization exists for the given folder and glob pattern; False otherwise.
        """
        summary_hash = hash_text(f"{ensure_endswith(folder, '/')}{glob}")
        return self._retriever is not None and Path(f"{PERSIST_DIR}/{summary_hash}").exists()

    def query(self, *queries: str) -> Optional[list[SummaryResult]]:
        """Answer questions about the summarized content.
        :param queries: The list queries to ask the AI engine.
        """
        if queries and self.retriever is not None:
            results: list[SummaryResult] = []
            for query in queries:
                if result := self._invoke(query):
                    results.append(result)
            return results
        return None

    def _invoke(self, query: str) -> Optional[SummaryResult]:
        """Query the AI retriever based on the summarized content. This method uses the provided query to retrieve
        information from a previously generated summary. If the query is valid and the AI engine returns a result, it
        creates a `SummaryResult` object with the summary details.
        :param query: The query string to be asked to the AI engine.
        :return: An object containing the summary details if the query is successful; otherwise, returns None.
        """
        if query and (result := self.retriever.invoke({"query": query})):
            return SummaryResult(self._folder, self._glob, *self.extract_result(result))
        return None


assert (summarizer := Summarizer().INSTANCE) is not None
