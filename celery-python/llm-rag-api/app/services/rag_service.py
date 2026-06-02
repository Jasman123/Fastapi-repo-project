
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.db.chroma import VectorStoreRepository
from app.core.config import get_settings
from app.models.schemas import SourceChunk, RAGQueryResponse


logger = logging.getLogger(__name__)

RAG_SYSTEM_PROMPT = """You are a helpful assistant answering questions based on provided context.

Rules:
1. Only use information from the provided context
2. If context doesn't contain the answer, say "I don't have enough information in my documents"
3. Be concise and accurate
4. Cite sources when relevant"""


class RAGService:
    
    def __init__(self):
        self._repo = VectorStoreRepository()
        self._settings = get_settings()
        
    def query(self, question: str, top_k: int = 3) -> RAGQueryResponse:
        logger.info(f"RAG query: '{question[:80]}'")
        results = self._repo.similarity_search(query = question, k=top_k)


        if not results:
            return RAGQueryResponse(
                question = question,
                answer = "No documents indexes yet. Please ingest documents first.",
                sources = [],
                model = self._settings.chat_model,
            )
        
        sources = [
            SourceChunk(
                doc_id=doc.metadata.get("doc_id", "unknown"),
                title=doc.metadata.get("title", "Untitled"),
                chunk_index=doc.metadata.get("chunk_index", -1),
                text=doc.page_content,
                similarity_score=round(1 - score, 4),
            )
            for doc, score in results
        ]

        context = "\n\n---\n\n".join(
            f"[Source {i+1}] ({s.title})\n{s.text}"
            for i, s in enumerate(sources)
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", RAG_SYSTEM_PROMPT),
            ("user", "Context:\n{context}\n\n---\n\nQuestion: {question}"),
        ])


        llm = ChatOpenAI(
            api_key = self._settings.openai_api_key,
            model = self._settings.chat_model,
            temperature = 0.3,
        )

        chain = prompt | llm | StrOutputParser()
        answer = chain.invoke({"context": context, "question": question})
        return RAGQueryResponse(
            question = question,
            answer = answer,
            sources = sources,
            model = self._settings.chat_model,
        )






