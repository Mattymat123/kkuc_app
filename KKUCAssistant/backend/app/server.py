from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, StreamingResponse
from langserve import add_routes
from .agent import agent_executor, KKUCAgent
from pydantic import BaseModel
from typing import List, Union, Dict, Any
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import json
import asyncio


class ChatInputType(BaseModel):
    messages: List[Union[HumanMessage, AIMessage, SystemMessage]]


app = FastAPI()

# Add CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins like ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")


# Direct chat endpoint that properly handles streaming
@app.post("/chat")
async def chat_endpoint(input_data: Dict[str, Any]):
    """Direct chat endpoint that handles streaming from LangGraph"""
    messages = input_data.get("messages", [])
    
    async def generate_stream():
        try:
            # Convert dict messages to LangChain message objects
            lc_messages = []
            for msg in messages:
                if isinstance(msg, dict):
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "user":
                        lc_messages.append(HumanMessage(content=content))
                    elif role == "assistant":
                        lc_messages.append(AIMessage(content=content))
                else:
                    lc_messages.append(msg)
            
            # Stream from the agent graph
            loop = asyncio.get_event_loop()
            
            # Use stream mode to get updates as they happen
            last_content = ""
            async for event in agent_executor.astream_events(
                {"messages": lc_messages},
                version="v1"
            ):
                kind = event.get("event")
                
                # Stream LLM tokens as they're generated
                if kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, 'content') and chunk.content:
                        # Send the token
                        yield f'0:{json.dumps(chunk.content)}\n'
                        last_content += chunk.content
                        await asyncio.sleep(0)  # Allow other tasks to run
            
            # Send completion marker
            yield 'd:{"finishReason":"stop"}\n'
            
        except Exception as e:
            print(f"Error in chat endpoint: {e}")
            import traceback
            traceback.print_exc()
            # Send error
            yield f'3:{json.dumps(str(e))}\n'
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain; charset=utf-8",
        headers={
            "X-Vercel-AI-Data-Stream": "v1",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# KKUC Agent with RAG workflow - deployed via LangServe
kkuc_agent_runnable = agent_executor.with_types(input_type=ChatInputType)
add_routes(app, kkuc_agent_runnable, path="/agent")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
