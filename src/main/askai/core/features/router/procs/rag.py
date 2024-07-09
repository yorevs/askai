import logging as log
from functools import lru_cache
from pathlib import Path
from typing import Optional

from hspylib.core.config.path_object import PathObject
from hspylib.core.metaclass.singleton import Singleton
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from askai.core.askai_configs import configs
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import PERSIST_DIR
from askai.core.component.summarizer import summarizer
from askai.core.support.langchain_support import lc_llm
from askai.core.support.utilities import hash_text
from askai.exception.exceptions import DocumentsNotFound


class Rag(metaclass=Singleton):
    """Processor to provide a answers from a RAG datasource."""

    INSTANCE: "Rag"

    DEFAULT_RAG_FILE: str = f"{prompt.PROMPT_DIR}/taius/taius-rag.txt"

    def __init__(self):
        self._retriever = None
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=configs.chunk_size, chunk_overlap=0)
        p_obj: PathObject = PathObject.of(self.DEFAULT_RAG_FILE)
        self._folder, self._glob = p_obj.abs_dir, p_obj.filename

    @property
    def persist_dir(self) -> Path:
        summary_hash = hash_text(self.sum_path)
        return Path(f"{PERSIST_DIR}/{summary_hash}")

    @property
    def sum_path(self) -> str:
        return f"{self._folder}{self._glob}"

    def process(self, question: str, **_) -> Optional[str]:
        """Process the user question to retrieve the final response.
        :param question: The user question to process.
        """
        self._generate()

        if (result := self._retriever.invoke({"query": question})) and (output := summarizer.extract_result(result)):
            return output[1]

        return msg.invalid_response(str(result))

    @lru_cache
    def _generate(self) -> None:
        embeddings = lc_llm.create_embeddings()

        if self.persist_dir.exists():
            log.info("Recovering vector store from: '%s'", self.persist_dir)
            v_store = Chroma(persist_directory=str(self.persist_dir), embedding_function=embeddings)
        else:
            log.info("Summarizing documents from '%s'", self.sum_path)
            documents: list[Document] = DirectoryLoader(
                self._folder, glob=self._glob, loader_cls=TextLoader).load()
            if len(documents) <= 0:
                raise DocumentsNotFound(f"Unable to find any document to summarize at: '{self.sum_path}'")
            splits: list[Document] = self._text_splitter.split_documents(documents)
            v_store = Chroma.from_documents(splits, embeddings, persist_directory=str(self.persist_dir))
        self._retriever = RetrievalQA.from_chain_type(
            llm=lc_llm.create_model(), chain_type="stuff", retriever=v_store.as_retriever()
        )


assert (rag := Rag().INSTANCE) is not None
