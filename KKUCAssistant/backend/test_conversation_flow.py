"""
Test script to verify conversation context flows correctly through the agent
"""
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_core.messages import HumanMessage, AIMessage
from app.agent import KKUCAgent

load_dotenv()


def test_conversation_context():
    """Test that conversation context is properly passed through the agent"""
    print("\n" + "="*80)
    print("Testing Conversation Context Flow")
    print("="*80)
    
    # Initialize agent
    agent = KKUCAgent()
    
    # Test 1: First query (should use RAG)
    print("\n📝 Test 1: Initial query about director")
    print("-" * 80)
    
    state1 = {
        "messages": [
            HumanMessage(content="Hvem er direktøren for KKUC?")
        ],
        "needs_rag": True
    }
    
    result1 = agent.graph.invoke(state1)
    print(f"\n✅ Response 1: {result1['messages'][-1].content[:200]}...")
    
    # Test 2: Follow-up query using pronoun (should use conversation context)
    print("\n\n📝 Test 2: Follow-up query with pronoun reference")
    print("-" * 80)
    
    state2 = {
        "messages": result1["messages"] + [
            HumanMessage(content="Hvad er hans telefonnummer?")
        ],
        "needs_rag": True
    }
    
    result2 = agent.graph.invoke(state2)
    print(f"\n✅ Response 2: {result2['messages'][-1].content[:200]}...")
    
    # Check if routing worked
    print("\n\n" + "="*80)
    print("Test Summary")
    print("="*80)
    print(f"Total messages in conversation: {len(result2['messages'])}")
    print(f"First query response length: {len(result1['messages'][-1].content)} chars")
    print(f"Second query response length: {len(result2['messages'][-1].content)} chars")
    
    # Verify conversation history was used
    if len(result2['messages']) >= 4:
        print("\n✅ Conversation history properly maintained")
    else:
        print("\n⚠️  Warning: Conversation history may not be complete")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    test_conversation_context()
