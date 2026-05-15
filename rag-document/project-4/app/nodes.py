from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .ingestion import embeddings, get_vectorstore
from .state import GraphState
from .config import settings


llm = ChatOpenAI( model = "gpt-4o-mini", temperature = 0.1, api_key = settings.OPENAI_API_KEY)
grader_llm = ChatOpenAI( model = "gpt-4o-mini", temperature = 0, api_key = settings.OPENAI_API_KEY)


def route_query(state: GraphState) -> GraphState:

    print(f"[NODE] route_query | q: {state['question'][:60]}...")

    router_prompt = ChatPromptTemplate.from_messages([
        ("system", """Classify the user question into one of three categories.
Reply with EXACTLY one word — nothing else.

Categories:
- rag          → question requires searching documents for factual info
- conversational → greeting, chitchat, thanks, or clarification of previous answer
- summarize    → user wants a summary of all or multiple documents"""),
        ("human", "Question: {question}"),
    ])

    chain = router_prompt | grader_llm | StrOutputParser()
    raw = chain.invoke({
        "question": state['question']
    }).strip().lower()

    query_type = 'rag'
    if 'conversational' in raw:
        query_type = 'conversational'
    elif 'summarize' in raw:
        query_type = 'summarize'

    print(f"[NODE] route_query | classified as: {query_type}")

    return {
        'query_type' : query_type,
        'original_question': state['question'],
        'rewrite_count': 0,
    }

def direct_llm(state: GraphState) -> GraphState:
    
    print(f"[NODE] direct_llm | type: {state['query_type']}")

    if state['query_type'] == 'conversational':
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant. Be concise and friendly."),
            *state.get("chat_history", []),
            ("human", "{question}"),
        ])
    else:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a document assistant.
The user wants a summary. Ask them to specify which document
they want summarized, or ingest documents first if none are available."""),
            ("human", "{question}"),
        ])

    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({'question': state['question']})
    new_history = [
        HumanMessage(content=state['question']),
        AIMessage(content=answer),
    ]

    return {
        'generation': answer,
        'chat_history': new_history,
        'documents': [],
        'answer_grade':'grounded',
    }


def retrieve(state: GraphState) -> GraphState:
    print(f"[NODE] retrieve | q: {state['question'][:60]}...")

    vectorstore = get_vectorstore()
    retriever = vectorstore.as_retriever(
        search_type='similiarity',
        search_kwargs = {'k' : settings.RETRIEVER_K},
    )
    documents = retriever.invoke(state['question'])
    print(f"[NODE] retrieve | found {len(documents)} chunks")

    return {'documents': documents}

def grade_documents(state:GraphState) -> GraphState:
    print(f"[NODE] grade_documents | chunks: {len(state['documents'])}")

    grader_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a relevance grader for a RAG system.
Assess if the document chunk is relevant to the user question.
Reply with EXACTLY one word: 'yes' or 'no'"""),
        ("human", "Document chunk:\n{document}\n\nQuestion: {question}"),
    ])

    chain = grader_prompt | grader_llm | StrOutputParser()
    relevant_docs = []

    for doc in state["documents"]:
        grade = chain.invoke({
            "document": doc.page_content[:500],   # trim for speed
            "question": state["question"],
        }).strip().lower()

        if 'yes' in grade:
            relevant_docs.append(doc)

    doc_grade = 'relevant' if relevant_docs else 'not relevant'
    print(f"[NODE] grade_documents | {len(relevant_docs)} relevant | grade: {doc_grade}")

    return {
        "documents": relevant_docs,
        "doc_grade": doc_grade,
    }

def rewrite_query(state: GraphState) -> GraphState:
    rewrite_count = state.get('rewrite_count', 0)+1
    print(f"[NODE] rewrite_query | attempt {rewrite_count}/{settings.MAX_REWRITE_ATTEMPTS}")

    rewriter_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a query rewriter for a document search system.
The original query did not find relevant documents.
Rewrite it to be more specific, use different keywords,
or expand abbreviations. Return ONLY the rewritten query."""),
        ("human", "Original query: {question}\n\nRewritten query:"),
    ])

    chain = rewriter_prompt | llm | StrOutputParser()
    rewritten = chain.invoke({'question': state['question']}).strip()
    print(f"[NODE] rewrite_query | '{state['question']}' → '{rewritten}'")

    return {
        "question":      rewritten,
        "rewrite_count": rewrite_count,
        "doc_grade":     "",           # reset grade so retrieve runs fresh
    }







