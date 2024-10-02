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
import glob
import os
import shutil
from pathlib import Path
from shutil import copyfile

from hspylib.core.config.path_object import PathObject
from hspylib.core.metaclass.classpath import AnyPath
from hspylib.core.preconditions import check_state
from hspylib.core.tools.commons import file_is_not_empty
from hspylib.core.tools.text_tools import hash_text, ensure_endswith
from langchain_community.document_loaders import CSVLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

from askai.__classpath__ import classpath
from askai.core.askai_configs import configs
from askai.core.askai_settings import ASKAI_DIR
from askai.core.support.langchain_support import lc_llm

# External RAG Directory
RAG_EXT_DIR: Path = Path(f"{ASKAI_DIR}/rag")
if not RAG_EXT_DIR.exists():
    RAG_EXT_DIR.mkdir(parents=True, exist_ok=True)


class RAGProvider:
    """A class responsible for implementing the Retrieval-Augmented Generation (RAG) mechanism."""

    RAG_DIR: Path = Path(os.path.join(classpath.resource_path(), "rag"))

    @staticmethod
    def copy_rag(path_name: AnyPath, dest_name: AnyPath | None = None) -> bool:
        """Copy the RAG documents into the AskAI RAG directory.
        :param path_name: The path of the RAG documents to copy.
        :param dest_name: The destination, within the RAG directory, where the documents will be copied to. If None,
                          defaults to a hashed directory based on the source path.
        :return: True if the copy operation was successful, False otherwise.
        """
        src_path: PathObject = PathObject.of(path_name)
        with open(f"{RAG_EXT_DIR}/rag-documents.txt", "w") as f_docs:
            docs: list[str] = list()
            if src_path.exists and src_path.is_file:
                file: str = f"{RAG_EXT_DIR}/{src_path.filename}"
                copyfile(str(src_path), file)
            elif src_path.exists and src_path.is_dir:
                shutil.copytree(
                    str(src_path),
                    str(RAG_EXT_DIR / (dest_name or hash_text(str(src_path))[:8])),
                    dirs_exist_ok=True,
                    symlinks=True
                )
            else:
                return False
            files: list[str] = glob.glob(f"{str(RAG_EXT_DIR)}/**/*.*", recursive=True)
            list(map(docs.append, files))
            f_docs.write("Available documents for RAG:" + os.linesep * 2)
            f_docs.writelines(set(ensure_endswith(d, os.linesep) for d in docs))

        return True

    def __init__(self, rag_filepath: str):
        self._rag_db = None
        self._rag_path: str = os.path.join(str(self.RAG_DIR), rag_filepath)
        self._rag_docs: list[Document] = CSVLoader(file_path=self._rag_path).load()
        self._rag_db: VectorStore | None = None
        check_state(file_is_not_empty(self._rag_path))

    def get_rag_examples(self, query: str, k: int = configs.rag_retrival_amount) -> str:
        """Retrieve a list of relevant examples based on the provided query.
        :param query: The search query used to retrieve examples.
        :param k: The number of examples to retrieve (default is 3).
        :return: A list of strings representing the retrieved examples.
        """
        if configs.is_rag:
            if self._rag_db is None:
                self._rag_db = FAISS.from_documents(self._rag_docs, lc_llm.create_embeddings())
            example_docs: list[Document] = self._rag_db.similarity_search(query, k=k)
            rag_examples: list[str] = [doc.page_content for doc in example_docs]
            return f"**Examples:**\n\"\"\"{(2 * os.linesep).join(rag_examples)}\"\"\""
