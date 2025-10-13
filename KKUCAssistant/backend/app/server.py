from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, StreamingResponse
from langserve import add_routes
from .agent import agent_executor, KKUCAgent
from pydantic import BaseModel
from typing import List, Union, Dict, Any, Optional
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import json
import asyncio
import uuid


class ChatInputType(BaseModel):
    messages: List[Union[HumanMessage, AIMessage, SystemMessage]]


class ThreadRunInput(BaseModel):
    input: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None
    stream_mode: Optional[str] = "values"


class ResumeInput(BaseModel):
    config: Optional[Dict[str, Any]] = None
    command: Optional[Dict[str, Any]] = None


app = FastAPI()

# Add CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")


@app.post("/threads/{thread_id}/runs/stream")
async def stream_run(thread_id: str, input_data: ThreadRunInput):
    """
    Stream a run for a specific thread - compatible with LangGraph SDK useStream()
    """
    print(f"\n🚀 Starting stream for thread: {thread_id}")
    
    async def generate_stream():
        try:
            # Prepare config with thread_id
            config = input_data.config or {}
            config["configurable"] = config.get("configurable", {})
            config["configurable"]["thread_id"] = thread_id
            
            print(f"📊 Config: {config}")
            print(f"📥 Input: {input_data.input}")
            
            # Stream events from the agent
            async for event in agent_executor.astream_events(
                input_data.input,
                config=config,
                version="v2"
            ):
                event_type = event.get("event")
                
                # Stream message chunks
                if event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        # Format as Server-Sent Events
                        yield f"event: message\ndata: {json.dumps({'content': chunk.content})}\n\n"
                
                # Stream interrupts
                elif event_type == "on_chain_end":
                    metadata = event.get("metadata", {})
                    if "langgraph_checkpoint_ns" in metadata:
                        # Check if there's an interrupt
                        data = event.get("data", {})
                        output = data.get("output", {})
                        
                        # Look for interrupt in the output
                        if isinstance(output, dict) and "__interrupt__" in output:
                            interrupt_data = output["__interrupt__"]
                            yield f"event: interrupt\ndata: {json.dumps(interrupt_data)}\n\n"
            
            # Send completion event
            yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"
            
        except Exception as e:
            print(f"❌ Error in stream: {e}")
            import traceback
            traceback.print_exc()
            error_data = {"error": str(e)}
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/threads/{thread_id}/runs")
async def resume_run(thread_id: str, resume_data: ResumeInput):
    """
    Resume a run from an interrupt - compatible with LangGraph SDK useStream()
    """
    print(f"\n▶️  Resuming thread: {thread_id}")
    print(f"📥 Command: {resume_data.command}")
    
    try:
        # Prepare config with thread_id
        config = resume_data.config or {}
        config["configurable"] = config.get("configurable", {})
        config["configurable"]["thread_id"] = thread_id
        
        # Get the resume value from command
        resume_value = None
        if resume_data.command and "resume" in resume_data.command:
            resume_value = resume_data.command["resume"]
        
        # Resume from interrupt with the value
        result = agent_executor.invoke(
            resume_value,  # Pass the resume value
            config=config
        )
        
        print(f"✅ Resume completed")
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        print(f"❌ Error resuming: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/threads/{thread_id}/state")
async def get_thread_state(thread_id: str):
    """
    Get the current state of a thread
    """
    print(f"\n📊 Getting state for thread: {thread_id}")
    
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = agent_executor.get_state(config)
        
        return {
            "values": state.values,
            "next": state.next,
            "metadata": state.metadata
        }
        
    except Exception as e:
        print(f"❌ Error getting state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Store thread IDs per session (in production, use Redis or database)
session_threads = {}

# Legacy endpoint for backward compatibility
@app.post("/chat")
async def chat_endpoint(input_data: Dict[str, Any]):
    """Legacy chat endpoint with thread persistence"""
    messages = input_data.get("messages", [])
    
    # Use a session identifier based on message history hash
    # This allows the same conversation to continue
    session_key = str(hash(str([m.get("content", "") if isinstance(m, dict) else str(m) for m in messages[:2]])))
    
    # Get or create thread ID for this session
    if session_key in session_threads:
        thread_id = session_threads[session_key]
        print(f"📌 Using existing thread: {thread_id}")
    else:
        thread_id = str(uuid.uuid4())
        session_threads[session_key] = thread_id
        print(f"🆕 Created new thread: {thread_id}")
    
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
            
            # Prepare config
            config = {"configurable": {"thread_id": thread_id}}
            
            # Stream the response
            streamed_tokens = False
            final_messages = []
            
            async for event in agent_executor.astream_events(
                {"messages": lc_messages},
                config=config,
                version="v2"
            ):
                event_type = event.get("event")
                
                # Stream LLM tokens
                if event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        yield f'0:{json.dumps(chunk.content)}\n'
                        streamed_tokens = True
                        await asyncio.sleep(0)
                
                # Capture final state to get non-LLM messages (like calendar responses)
                elif event_type == "on_chain_end":
                    data = event.get("data", {})
                    output = data.get("output", {})
                    if isinstance(output, dict) and "messages" in output:
                        final_messages = output["messages"]
            
            # If no tokens were streamed (e.g., calendar booking), stream the final message
            if not streamed_tokens and final_messages:
                for msg in final_messages:
                    if isinstance(msg, AIMessage) and msg.content:
                        # Stream the complete message
                        yield f'0:{json.dumps(msg.content)}\n'
                        await asyncio.sleep(0)
            
            # Send completion marker
            yield 'd:{"finishReason":"stop"}\n'
            
        except Exception as e:
            print(f"Error in chat endpoint: {e}")
            import traceback
            traceback.print_exc()
            error_msg = f"Error: {str(e)}"
            yield f'0:{json.dumps(error_msg)}\n'
            yield 'd:{"finishReason":"error"}\n'
    
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
