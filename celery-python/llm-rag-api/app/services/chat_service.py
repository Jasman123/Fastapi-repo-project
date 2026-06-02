import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.core.config import get_settings


logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant. Answer concisely and accurately."

class ChatService:
    def __init__(self):
        self._settings = get_settings()

    def _get_llm(self, temperature: float = 0.7) -> ChatOpenAI:
        return ChatOpenAI(
            api_key = self._settings.openai_api_key,
            model = self._settings.chat_model,
            temperature = temperature,
        )

    def ask (self, question: str, system_prompt: str | None = None, temperature: float = 0.7) -> dict:
        logger.info(f"Chat ask: '{question[:80]}'")
        llm = self._get_llm(temperature = temperature)
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt or DEFAULT_SYSTEM_PROMPT),
            ("user", question),
        ])
        chain = prompt | llm | StrOutputParser()
        answer = chain.invoke({})
        return {
            "question": question,
            "answer": answer,
            "model": self._settings.chat_model,
        }
    
    def summarize(self, text: str, max_sentences: int = 3) -> dict:
        logger.info(f"Summarize: {len(text)} chars")
        llm = self._get_llm(temperature = 0.3)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert summarizer. Summarize in exactly {max_sentences} sentences."),
            ("user", "Text:\n\n{text}"),
        ])
        chain = prompt | llm | StrOutputParser()
        summary = chain.invoke({"text": text, "max_sentences": max_sentences})

        return {
            "original_length": len(text),
            "summary": summary,
            "summary_length": len(summary),
            "compression_ratio": round(len(summary)/ len(text), 3),
        }





