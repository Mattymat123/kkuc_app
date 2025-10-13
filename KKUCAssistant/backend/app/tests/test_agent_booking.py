"""
Test the agent booking flow end-to-end
"""
from app.agent import KKUCAgent
from langchain_core.messages import HumanMessage

def test_agent_booking_flow():
    """Test that the agent can handle a booking request"""
    
    print("\n" + "="*60)
    print("Testing Agent Booking Flow")
    print("="*60)
    
    # Initialize agent
    agent = KKUCAgent()
    
    # Step 1: Initial booking request
    print("\n📝 Step 1: User requests to book an appointment...")
    initial_state = {
        "messages": [HumanMessage(content="Jeg vil gerne booke en tid")],
        "booking_state": None
    }
    
    try:
        result = agent.graph.invoke(initial_state)
        
        print(f"\n✅ Agent Response:")
        if result["messages"]:
            last_message = result["messages"][-1]
            print(f"   {last_message.content[:200]}...")
        
        print(f"\n📊 Booking State:")
        booking_state = result.get("booking_state")
        if booking_state:
            print(f"   Step: {booking_state.get('step')}")
            print(f"   Available slots: {len(booking_state.get('available_slots', []))}")
            if booking_state.get('available_slots'):
                print(f"   First slot: {booking_state['available_slots'][0]}")
        else:
            print("   No booking state")
        
        # Check if we got available slots
        if booking_state and booking_state.get("available_slots"):
            print("\n✅ SUCCESS! Agent successfully fetched available slots")
            print(f"   Found {len(booking_state['available_slots'])} slots")
            return True
        else:
            print("\n❌ FAILED! No available slots returned")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_agent_booking_flow()
    exit(0 if success else 1)
