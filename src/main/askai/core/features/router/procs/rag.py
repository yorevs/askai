from functools import lru_cache

from askai.core.askai_configs import configs
from askai.core.askai_messages import msg
from askai.core.component.cache_service import RAG_DIR
from askai.core.engine.openai.temperature import Temperature
from askai.core.support.langchain_support import lc_llm
from hspylib.core.metaclass.singleton import Singleton
from langchain import hub
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter


class Rag(metaclass=Singleton):
    """Processor to provide a answers from a RAG datasource."""

    INSTANCE: "Rag"

    def __init__(self):
        self._rag_chain = None
        self._vectorstore = None
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=configs.chunk_size, chunk_overlap=0)

    def process(self, question: str, **_) -> str:
        """Process the user question to retrieve the final response.
        :param question: The user question to process.
        """
        self._generate()

        if output := self._rag_chain.invoke(question):
            return output

        self._vectorstore.delete_collection()

        return msg.invalid_response(output)

    @lru_cache
    def _generate(self) -> None:
        loader: DirectoryLoader = DirectoryLoader(str(RAG_DIR))
        rag_docs: list[Document] = loader.load()
        llm = lc_llm.create_model(temperature=Temperature.DATA_ANALYSIS.temp)
        embeddings = lc_llm.create_embeddings()
        splits = self._text_splitter.split_documents(rag_docs)

        self._vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)
        retriever = self._vectorstore.as_retriever()
        rag_prompt = hub.pull("rlm/rag-prompt")

        def _format_docs_(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        self._rag_chain = (
            {"context": retriever | _format_docs_, "question": RunnablePassthrough()}
            | rag_prompt
            | llm
            | StrOutputParser()
        )


assert (rag := Rag().INSTANCE) is not None
