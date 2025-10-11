"""
Test script for RAG Agent
Run this to test the RAG pipeline with sample queries
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agent import KKUCAgent
from langchain_core.messages import HumanMessage


def test_rag_agent():
    """Test the simplified RAG agent with sample queries"""
    
    print("\n" + "="*80)
    print("🧪 TESTING SIMPLIFIED KKUC RAG AGENT")
    print("="*80 + "\n")
    
    # Sample test queries in Danish
    test_queries = [
        "Hvem er forperson for KKUC?",
        "Hvad er behandlingsmulighederne for stofmisbrug?",
        "Hvordan kontakter jeg KKUC?",
    ]
    
    # Initialize agent
    print("Initializing agent...")
    agent = KKUCAgent()
    print("✓ Agent initialized\n")
    
    # Test each query
    for i, query in enumerate(test_queries, 1):
        print("\n" + "-"*80)
        print(f"TEST {i}/{len(test_queries)}")
        print("-"*80)
        print(f"Query: {query}\n")
        
        try:
            # Run through agent (simplified workflow always runs RAG)
            state = {"messages": [HumanMessage(content=query)]}
            result_state = agent.process_query_node(state)
            
            print("\n📊 RESULT:")
            print(result_state["messages"][-1].content)
            print("\n" + "="*80)
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("✅ TESTING COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_rag_agent()
