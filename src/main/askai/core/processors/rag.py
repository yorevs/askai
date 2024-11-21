#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.processors.rag
      @file: rag.py
   @created: Fri, 5 May 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from clitt.core.term.cursor import cursor
from rich.live import Live
from rich.spinner import Spinner

from askai.core.askai_configs import configs
from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import PERSIST_DIR
from askai.core.component.rag_provider import RAG_EXT_DIR, RAGProvider
from askai.core.engine.openai.temperature import Temperature
from askai.core.model.ai_reply import AIReply
from askai.core.support.langchain_support import lc_llm
from askai.exception.exceptions import DocumentsNotFound, TerminatingQuery
from askai.core.support.text_formatter import text_formatter as tf
from functools import lru_cache
from hspylib.core.config.path_object import PathObject
from hspylib.core.metaclass.classpath import AnyPath
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.text_tools import hash_text
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import BasePromptTemplate, ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
from rich.status import Status
from typing import Optional

import logging as log
import os
import shutil


class Rag(metaclass=Singleton):
    """Processor to provide a answers from a RAG datasource."""

    INSTANCE: "Rag"

    def __init__(self):
        self._rag_chain: Runnable | None = None
        self._vectorstore: Chroma | None = None
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=configs.chunk_size, chunk_overlap=configs.chunk_overlap
        )

    @property
    def rag_template(self) -> BasePromptTemplate:
        prompt_file: PathObject = PathObject.of(prompt.append_path(f"taius/taius-non-interactive"))
        final_prompt: str = prompt.read_prompt(prompt_file.filename, prompt_file.abs_dir)
        # fmt: off
        return ChatPromptTemplate.from_messages([
            ("system", final_prompt),
            ("user", "{question}"),
            ("user", "{context}")
        ])
        # fmt: on

    @lru_cache
    def persist_dir(self, rag_dir: AnyPath, file_glob: AnyPath) -> Path:
        """TODO"""
        summary_hash = hash_text(os.path.join(rag_dir, file_glob))
        return Path(os.path.join(str(PERSIST_DIR), summary_hash))

    def process(self, question: str, **_) -> Optional[str]:
        """Process the user question to retrieve the final response.
        :param question: The user question to process.
        :return: The final response after processing the question.
        """
        if not question:
            raise TerminatingQuery("The user wants to exit!")
        if question.casefold() in ["exit", "leave", "quit", "q"]:
            events.reply.emit(reply=AIReply.info(msg.leave_rag()))
            events.mode_changed.emit(mode="DEFAULT")
            return None

        # FIXME Include kwargs to specify rag dir and glob
        self.generate()

        with Live(Spinner("dots", f"[green]{msg.wait()}[/green]", style="green"), console=tf.console):
            if not (output := self._rag_chain.invoke(question)):
                output = msg.invalid_response(output)

        cursor.erase_line()

        return output

    def generate(self, rag_dir: AnyPath = RAG_EXT_DIR, file_glob: AnyPath = "**/*.md") -> None:
        """Generates RAG data from the specified directory.
        :param rag_dir: The directory containing the files for RAG data generation
        :param file_glob: The files from which to generate the RAG database.
        :return: None
        """
        if not self._rag_chain:
            # Check weather the rag directory requires update.
            if RAGProvider.requires_update(RAG_EXT_DIR):
                rag_db_dir: Path = self.persist_dir(rag_dir, file_glob)
                shutil.rmtree(str(rag_db_dir), ignore_errors=True)

            embeddings = lc_llm.create_embeddings()
            llm = lc_llm.create_chat_model(temperature=Temperature.DATA_ANALYSIS.temp)
            persist_dir: Path = self.persist_dir(rag_dir, file_glob)
            if persist_dir.exists() and persist_dir.is_dir():
                log.info("Recovering vector store from: '%s'", persist_dir)
                self._vectorstore = Chroma(persist_directory=str(persist_dir), embedding_function=embeddings)
            else:
                with Status(f"[green]{msg.summarizing()}[/green]"):
                    rag_docs: list[Document] = DirectoryLoader(str(rag_dir), glob=file_glob, recursive=True).load()
                    if len(rag_docs) <= 0:
                        raise DocumentsNotFound(f"Unable to find any document to at: '{persist_dir}'")
                    self._vectorstore = Chroma.from_documents(
                        persist_directory=str(persist_dir),
                        documents=self._text_splitter.split_documents(rag_docs),
                        embedding=embeddings,
                    )

            retriever = self._vectorstore.as_retriever()
            rag_prompt = self.rag_template

            def _format_docs_(docs):
                return "\n\n".join(doc.page_content for doc in docs)

            self._rag_chain = (
                {"context": retriever | _format_docs_, "question": RunnablePassthrough()}
                | rag_prompt
                | llm
                | StrOutputParser()
            )
        return self._rag_chain


assert (rag := Rag().INSTANCE) is not None
