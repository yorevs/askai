import logging as log
import os
from pathlib import Path
from typing import Optional

from askai.core.askai_configs import configs
from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import RAG_DIR, PERSIST_DIR
from askai.core.engine.openai.temperature import Temperature
from askai.core.model.ai_reply import AIReply
from askai.core.support.langchain_support import lc_llm
from askai.core.support.spinner import Spinner
from askai.exception.exceptions import DocumentsNotFound, TerminatingQuery
from hspylib.core.config.path_object import PathObject
from hspylib.core.metaclass.classpath import AnyPath
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.text_tools import hash_text
from hspylib.modules.cli.vt100.vt_color import VtColor
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import BasePromptTemplate, ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter


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
        prompt_file: PathObject = PathObject.of(prompt.append_path(f"langchain/rag-prompt"))
        final_prompt: str = prompt.read_prompt(prompt_file.filename, prompt_file.abs_dir)
        # fmt: off
        return ChatPromptTemplate.from_messages([
            ("system", final_prompt),
            ("user", "{question}"),
            ("user", "{context}")
        ])
        # fmt: on

    def persist_dir(self, file_glob: AnyPath) -> Path:
        """TODO"""
        summary_hash = hash_text(file_glob)
        return Path(f"{PERSIST_DIR}/{summary_hash}")

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

        self.generate()

        if not (output := self._rag_chain.invoke(question)):
            output = msg.invalid_response(output)

        return output

    def generate(self, file_glob: str = "**/*.md") -> None:
        """Generates RAG data from the specified directory.
        :param file_glob: The files from which to generate the RAG database.
        """
        if not self._rag_chain:
            embeddings = lc_llm.create_embeddings()
            llm = lc_llm.create_chat_model(temperature=Temperature.DATA_ANALYSIS.temp)
            persist_dir: str = str(self.persist_dir(file_glob))
            if os.path.exists(persist_dir):
                log.info("Recovering vector store from: '%s'", persist_dir)
                self._vectorstore = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
            else:
                with Spinner.COLIMA.run(suffix=msg.loading("documents"), color=VtColor.GREEN) as spinner:
                    spinner.start()
                    rag_docs: list[Document] = DirectoryLoader(str(RAG_DIR), glob=file_glob, recursive=True).load()
                    spinner.stop()
                if len(rag_docs) <= 0:
                    raise DocumentsNotFound(f"Unable to find any document to at: '{persist_dir}'")
                self._vectorstore = Chroma.from_documents(
                    persist_directory=persist_dir,
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
