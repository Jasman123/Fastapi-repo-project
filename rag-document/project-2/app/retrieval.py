from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document


from .config import settings
from .ingestion import get_vectorstore

embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=settings.OPENAI_API_KEY)
llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=settings.OPENAI_API_KEY, temperature=0.1)

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful assistant that answers questions \
based strictly on the provided context.

If the answer is not found in the context, say:
"I don't have enough information to answer that from the provided documents."

Always cite which source document your answer comes from.

Context:
{context}"""),
    ("human", "{question}"),
])


def format_docs(docs: list[Document]) -> str:
    # Output example:
    # [Source: myfile.pdf, Page: 2]
    # FastAPI is a modern web framework...
    formated_docs = []

    for doc in docs:
        source = doc.metadata.get("source", "unknown source")
        page = doc.metadata.get("page", "")
        header = f'[Source: {source}'+ (f', Page: {page+1}' if page != "" else '') + ']'
        formated_docs.append(f"{header}\n{doc.page_content}")

    return "\n\n".join(formated_docs)

def build_rag_chain(vectorstore: Chroma):

    retriever = vectorstore.as_retriever(
        search_type = "similarity",
        search_kwargs = {"k": settings.TOP_K},
    )

    chain =(
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough()
        }
        | RAG_PROMPT
        | llm
        | StrOutputParser()
    )

    return chain, retriever

async def query_documents(question: str, vectorstore: Chroma) -> dict:
    if not vectorstore._collection.count():
        return {"answer": "No documents have been ingested yet. Please upload a document first.",
                "source": [],
                "chunks_used": 0,   
                }
    
    chain, retriever = build_rag_chain(vectorstore)
    answer = await chain.ainvoke(question)
    source_docs = await retriever.ainvoke(question)
    sources = list({
        doc.metadata.get("source", "unknown source") for     doc in source_docs
    })

    return {
        "answer": answer,
        "source": sources,
        "chunks_used": len(source_docs)
    }

    

   
    


