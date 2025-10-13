"""
Test script for Agent Routing with LLM-based intent classification
Tests both calendar booking and RAG search routing
"""
from app.agent import KKUCAgent
from langchain_core.messages import HumanMessage


def test_routing():
    """Test the LLM-based routing"""
    print("\n" + "="*60)
    print("🧪 Testing Agent Routing with LLM Intent Classification")
    print("="*60)
    
    agent = KKUCAgent()
    
    # Test cases
    test_cases = [
        ("Jeg vil gerne booke en tid", "calendar"),
        ("Book din første tid", "calendar"),
        ("Hvornår kan jeg komme?", "calendar"),
        ("Hvad er KKUC?", "rag"),
        ("Hvordan virker behandlingen?", "rag"),
        ("Fortæl mig om misbrugsbehandling", "rag"),
    ]
    
    print("\n📋 Testing routing for different queries:\n")
    
    for query, expected_route in test_cases:
        print(f"Query: '{query}'")
        print(f"Expected: {expected_route}")
        
        # Create state with the query
        state = {
            "messages": [HumanMessage(content=query)]
        }
        
        # Test routing
        actual_route = agent.should_use_calendar(state)
        
        status = "✅" if actual_route == expected_route else "❌"
        print(f"Actual: {actual_route} {status}")
        print("-" * 60)
    
    print("\n" + "="*60)
    print("✅ Routing test complete!")
    print("="*60)


if __name__ == "__main__":
    test_routing()
