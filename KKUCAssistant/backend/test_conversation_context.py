"""
Test script to verify conversation context and intelligent routing
"""
import asyncio
from langchain_core.messages import HumanMessage, AIMessage
from app.agent import agent_executor


async def test_conversation_flow():
    """Test the conversation flow with follow-up questions"""
    
    print("="*60)
    print("Testing Conversation Context & Intelligent Routing")
    print("="*60)
    
    # Test 1: Initial question requiring RAG
    print("\n📝 Test 1: Initial question about director")
    print("-" * 60)
    
    state1 = {
        "messages": [
            HumanMessage(content="Hvem er jeres direktør?")
        ]
    }
    
    result1 = await agent_executor.ainvoke(state1)
    print(f"\nUser: Hvem er jeres direktør?")
    print(f"Assistant: {result1['messages'][-1].content}")
    
    # Test 2: Follow-up question that should use context (not RAG)
    print("\n\n📝 Test 2: Follow-up question about phone number")
    print("-" * 60)
    
    state2 = {
        "messages": result1["messages"] + [
            HumanMessage(content="Hvad er hans nummer?")
        ]
    }
    
    result2 = await agent_executor.ainvoke(state2)
    print(f"\nUser: Hvad er hans nummer?")
    print(f"Assistant: {result2['messages'][-1].content}")
    
    # Test 3: Another follow-up
    print("\n\n📝 Test 3: Another follow-up about email")
    print("-" * 60)
    
    state3 = {
        "messages": result2["messages"] + [
            HumanMessage(content="Og hans email?")
        ]
    }
    
    result3 = await agent_executor.ainvoke(state3)
    print(f"\nUser: Og hans email?")
    print(f"Assistant: {result3['messages'][-1].content}")
    
    # Test 4: New question requiring RAG
    print("\n\n📝 Test 4: New question requiring RAG search")
    print("-" * 60)
    
    state4 = {
        "messages": result3["messages"] + [
            HumanMessage(content="Hvad er åbningstiderne?")
        ]
    }
    
    result4 = await agent_executor.ainvoke(state4)
    print(f"\nUser: Hvad er åbningstiderne?")
    print(f"Assistant: {result4['messages'][-1].content}")
    
    print("\n" + "="*60)
    print("✅ Test completed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_conversation_flow())
