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
        search_type='similarity',
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

def generate(state:GraphState) -> GraphState:
    print(f"[NODE] generate | docs: {len(state['documents'])}")
    if state['documents']:
        context = '\n\n---\n\n'.join(
            f'[source: {doc.metadata.get("filename", "?")}]'
            f'page {doc.metadata.get("page", "?")}'
            f'{doc.page_content}'
            for doc in state['documents']
        )
    else:
        context = "No relevant documents found in the knowledge base."

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a precise document assistant.
Answer the question using ONLY the context provided.
If the context does not contain enough information, say:
"The documents don't contain enough information to answer this."
Always mention which document/page your answer comes from."""),
        *state.get("chat_history", []),
        ("human", "Context:\n{context}\n\nQuestion: {question}"),
    ])

    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({
        'context': context,
        'question': state['original_question'],
    })

    new_history = [
        HumanMessage(content = state['original_question']),
        AIMessage(content = answer)
    ]

    return {
        'generation': answer,
        'chat_history': new_history,
        'answer_grade':''
    }

def grade_answer(state:GraphState) -> GraphState:
    print(f"[NODE] grade_answer | checking groundedness...")

    if not state['documents']:
        return {'answer_grade': 'grounded'}
    

    grader_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a hallucination grader.
    Check if the answer is fully supported by the provided context.
    Reply with EXACTLY one word: 'grounded' or 'hallucinated'"""),
            ("human", """Context:
    {context}

    Answer:
    {answer}"""),
    ])

    context = '\n\n'.join(d.page_content for d in state['document'])
    chain = grade_answer | grader_llm | StrOutputParser()
    grade = chain.invoke({
        'context': context[:3000],
        'answer': state['generation'],

    }).strip().lower()

    answer_grade = 'grounded' if 'grounded' in grade else 'hallucinated'
    print(f"[NODE] grade_answer | {answer_grade}")

    return {"answer_grade": answer_grade}

def regenerate(state: GraphState) -> GraphState:
    print(f"[NODE] regenerate | retrying with stricter prompt...")
    
    context = '\n\n---\n\n'.join(
        doc.page_content for doc in state['documents']
    )

    stric_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an extremely precise document assistant.
    STRICT RULES:
    1. Use ONLY information explicitly stated in the context below
    2. Do NOT add any information from your training knowledge
    3. If the answer is not in the context, say exactly:
    "This information is not available in the provided documents."
    4. Quote directly from the context where possible"""),
            ("human", "Context:\n{context}\n\nQuestion: {question}"),
    ])
    chain = stric_prompt | llm | StrOutputParser()
    answer = chain.invoke({
        'context': context,
        'question': state['original_question'],
    })

    new_history = [
        HumanMessage(content=state["original_question"]),
        AIMessage(content=answer),
    ]

    return {
        "generation":   answer,
        "chat_history": new_history,
        "answer_grade": "grounded",   # force end — don't loop again
    }


# CONDITIONAL EDGE FUNCTIONS — pure routing logic


def route_after_query_classification(state: GraphState) -> str:
    query_type = state.get('query_type','rag')
    if query_type in ('conversational', 'summarize'):
        return 'direct_llm'
    return 'retrieve'

def route_after_grading(state: GraphState)-> str:
    doc_grade = state.get('doc_grade', 'relevant')
    rewrite_count = state.get('rewrite_count', 0)

    if doc_grade == 'not_relevant' and rewrite_count < settings.MAX_REWRITE_ATTEMPTS:
        return 'rewrite_query'
    return 'generate'

def route_after_answer_grading(state: GraphState) -> str:
    grade = state.get('answer_grade', 'grounded')
    if grade == 'hallucinated':
        return 'regenerate'
    return 'end'










