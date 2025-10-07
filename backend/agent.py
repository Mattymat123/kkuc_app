"""
Build your LangChain agent here
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
import json
from typing import List, Dict, AsyncGenerator


async def stream_agent_response(messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
    """Stream response from your agent"""
    
    # Simple prompt - customize this
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant for KKUC. Be concise and friendly."),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    # LLM
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7, streaming=True)
    
    # Chain
    chain = prompt | llm | StrOutputParser()
    
    try:
        # Format messages
        formatted = [(m["role"], m["content"]) for m in messages]
        
        # Stream chunks
        async for chunk in chain.astream({"messages": formatted}):
            yield f"data: {json.dumps({'type': 'text-delta', 'textDelta': chunk})}\n\n"
        
        # Finish
        yield f"data: {json.dumps({'type': 'finish', 'finishReason': 'stop'})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"