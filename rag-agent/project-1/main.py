from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain.agents import create_agent
from langchain.tools import tool
import math
from config import settings


app = FastAPI(title='Simple ReaAct Agent')

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=settings.OPENAI_API_KEY)

@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression. Supports standard math functions (sin, cos, sqrt, etc.)."""
    try:
        allowed = {
            k: v for k, v in math.__dict__.items()
            if not k.startswith("_")
        }
        result = eval(expression, {"__builtins__":{}}, allowed)
        return f'Result: {result}'
    except Exception as e:
        return f'Calculation error: {e}. Check the expression syntax.'
    
@tool
def get_weather(city: str) -> str:
    """Get current weather for a city. Supported cities: Jakarta, Hong Kong, London, Tokyo."""
    weather_data = {
        "jakarta":   {"temp": 31, "condition": "thunderstorm", "humidity": 89},
        "hong kong": {"temp": 24, "condition": "partly cloudy", "humidity": 72},
        "london":    {"temp": 12, "condition": "rainy",         "humidity": 85},
        "tokyo":     {"temp": 18, "condition": "clear",         "humidity": 60},
    }

    city_lower = city.lower()
    data = weather_data.get(city_lower)

    if not data:
        return f'Weather data not available for "{city}". Try: Jakarta, Hong Kong, London, Tokyo.'
    
    return (
        f"Weather in {city}: {data['temp']}°C, "
        f"{data['condition']}, humidity {data['humidity']}%"
    )

@tool
def search_knowledge(query: str) -> str:
    """Search a knowledge base about: FastAPI, ReAct, RAG, Milvus, LangChain."""
    knowledge = {
        "fastapi": "FastAPI is a modern Python web framework built on Starlette. It supports async natively, auto-generates OpenAPI docs, and uses Pydantic for validation. Created by Sebastián Ramírez in 2018.",
        "react":   "ReAct (Reasoning + Acting) is an agent architecture where an LLM alternates between Thought, Action, and Observation steps to solve tasks requiring multiple tool calls.",
        "rag":     "RAG (Retrieval Augmented Generation) combines vector search with LLM generation. Documents are embedded and stored in a vector DB. At query time, relevant chunks are retrieved and stuffed into the prompt.",
        "milvus":  "Milvus is an open-source vector database built for AI applications. It supports billions of vectors, HNSW indexing, and is used in production by Salesforce, Shopee, and eBay.",
        "langchain": "LangChain is a Python framework for building LLM applications. It provides tools, chains, agents, and memory abstractions that simplify working with language models.",
    }

    query_lower = query.lower()
    for key, value in knowledge.items():
        if key in query_lower or query_lower in key:
            return value
    return f'No specific information found or "{query}". Try Try: FastAPI, ReAct, RAG, Milvus, LangChain. '


tools = [calculator, get_weather, search_knowledge]

agent = create_agent(
    model=llm,
    tools=tools,
)


#schema

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    question: str

@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail='Question can not be empty')

    try:
        result = agent.invoke({"messages": [("user", request.question)]})
        return AskResponse(
            answer=result["messages"][-1].content,
            question=request.question,
        )
    except Exception as e:
        raise HTTPException(status_code = 500, detail=str(e))
    
@app.get("/tools")
def list_tools():
    return {
        "tools": [
            {
                "name":        t.name,
                "description": t.description,
            }
            for t in tools
        ]
    }

@app.get("/health")
def health():
    return {"status": "ok", "agent": "ReAct", "tools": len(tools)}





