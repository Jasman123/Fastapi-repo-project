from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from qdrant_client import QdrantClient
from .state import GraphState
from .config import settings
from langchain_core.documents import Document


embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=settings.OPENAI_API_KEY)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, openai_api_key=settings.OPENAI_API_KEY, streaming=True)
grader_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=settings.OPENAI_API_KEY)
qdrant_client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY,)
vectorstore = QdrantVectorStore(client=qdrant_client, collection_name=settings.QDRANT_COLLECTION, embedding=embeddings, )


def retrieve(state: GraphState)-> GraphState:

    print(f"[NODE] retrieve | question: {state['question'][:50]}...")
    
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.RETRIEVER_K}
    )

    documents = retriever.invoke(state['question'])
    return {'documents' : documents}

def grade_document(state: GraphState) -> GraphState:

    print(f"[NODE] grade_documents | chunks: {len(state['documents'])}")

    grader_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a relevance grader.
Assess if the retrieved document chunk is relevant to the question.
Reply with exactly one word: 'relevant' or 'not_relevant'"""),
        ("human", "Document: {document}\n\nQuestion: {question}"),
    ])

    grader_chain = grader_prompt | grader_llm | StrOutputParser()
    relevant_docs = []

    for doc in state['documents']:
        grade = grader_chain.invoke({
            "document": doc.page_content,
            "question": state['question']
        }).strip().lower()

        if grade == "relevant":
            relevant_docs.append(doc)

    needs_web = len(relevant_docs) == 0

    print(f"[NODE] grade_documents | relevant: {len(relevant_docs)} | web_search: {needs_web}")

    return {
        "documents": relevant_docs,
        "web_search": needs_web,
        "doc_grade": "not_relevant" if needs_web else "relevant",
    }

def web_search_node(state: GraphState) -> GraphState:
    print(f"[NODE] web_search | question: {state['question'][:50]}...")
    fallback_doc = Document(
        page_content=(
            "No relevant information was found in the uploaded documents. "
            "Please upload documents that contain information about this topic."
        ),
        metadata={"source": "fallback", "page": 0},
    )

    return {"documents": [fallback_doc], "web_search": True}

def generate(state: GraphState) -> GraphState:
    print(f"[NODE] generate | docs: {len(state['documents'])} ")

    context = "\n\n---\n\n".join(
        f"source: {doc.metadata.get('filename','?')}"
        f"p.{doc.metadata.get('page','?')}\n {doc.page_content}"
        for doc in state["documents"]
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful document assistant.
Answer the question using ONLY the context provided.
If the answer is not in context, say so clearly.
Always cite your sources."""),
        # Inject conversation history as a placeholder
        # LangChain fills this with the actual message list
        *state.get("chat_history", []),
        ("human", "Context:\n{context}\n\nQuestion: {question}"),
    ])

    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({
        "context": context,
        "question": state["question"],
    })

    new_history = [
        HumanMessage(content=state["question"]),
        AIMessage(content=answer),
    ]
    return {
        "generation": answer,
        "chat_history" : new_history,
    }


def route_after_grading(state: GraphState) -> str:

    if state.get("web_search", False):
        print("[ROUTE] → web_search")
        return "web_search"
    print("[ROUTE] → generate")
    return "generate"



    