"""
Test the complete agent booking flow end-to-end
Simulates a full user interaction: request → select → confirm → book
"""
from app.agent import KKUCAgent
from langchain_core.messages import HumanMessage, AIMessage

def test_full_agent_booking_flow():
    """Test the complete agent booking flow with all steps"""
    
    print("\n" + "="*60)
    print("Testing Complete Agent Booking Flow")
    print("="*60)
    
    # Initialize agent
    agent = KKUCAgent()
    
    # Step 1: Initial booking request
    print("\n📝 Step 1: User requests to book an appointment...")
    state = {
        "messages": [HumanMessage(content="Jeg vil gerne booke en tid")],
        "booking_state": None
    }
    
    try:
        result = agent.graph.invoke(state)
        
        print(f"\n✅ Agent Response (Step 1):")
        if result["messages"]:
            last_message = result["messages"][-1]
            print(f"   {last_message.content[:150]}...")
        
        booking_state = result.get("booking_state")
        if not booking_state or not booking_state.get("available_slots"):
            print("\n❌ FAILED at Step 1: No available slots")
            return False
        
        print(f"\n✅ Step 1 SUCCESS: Found {len(booking_state['available_slots'])} slots")
        print(f"   Current step: {booking_state.get('step')}")
        
        # Step 2: User selects a slot (select slot #1)
        print("\n📝 Step 2: User selects slot #1...")
        state = {
            "messages": result["messages"] + [HumanMessage(content="1")],
            "booking_state": booking_state
        }
        
        result = agent.graph.invoke(state)
        
        print(f"\n✅ Agent Response (Step 2):")
        if result["messages"]:
            last_message = result["messages"][-1]
            print(f"   {last_message.content[:150]}...")
        
        booking_state = result.get("booking_state")
        if not booking_state or booking_state.get("step") != "confirm":
            print(f"\n❌ FAILED at Step 2: Expected 'confirm' step, got '{booking_state.get('step') if booking_state else 'None'}'")
            return False
        
        selected_slot = booking_state.get("selected_slot")
        if not selected_slot:
            print("\n❌ FAILED at Step 2: No slot selected")
            return False
        
        print(f"\n✅ Step 2 SUCCESS: Slot selected")
        print(f"   Selected: {selected_slot['day']}, {selected_slot['date']} at {selected_slot['time']}")
        print(f"   Current step: {booking_state.get('step')}")
        
        # Step 3: User confirms the booking
        print("\n📝 Step 3: User confirms booking...")
        state = {
            "messages": result["messages"] + [HumanMessage(content="ja")],
            "booking_state": booking_state
        }
        
        result = agent.graph.invoke(state)
        
        print(f"\n✅ Agent Response (Step 3):")
        if result["messages"]:
            last_message = result["messages"][-1]
            print(f"   {last_message.content[:200]}...")
        
        booking_state = result.get("booking_state")
        if not booking_state or booking_state.get("step") != "complete":
            print(f"\n❌ FAILED at Step 3: Expected 'complete' step, got '{booking_state.get('step') if booking_state else 'None'}'")
            return False
        
        booking_result = booking_state.get("booking_result")
        if not booking_result:
            print("\n❌ FAILED at Step 3: No booking result")
            return False
        
        if booking_result.get("status") != "confirmed":
            print(f"\n❌ FAILED at Step 3: Booking not confirmed, status: {booking_result.get('status')}")
            return False
        
        print(f"\n✅ Step 3 SUCCESS: Booking confirmed!")
        print(f"   Event ID: {booking_result.get('event_id')}")
        print(f"   Name: {booking_result.get('name')}")
        print(f"   Description: {booking_result.get('description')}")
        print(f"   Date: {booking_result.get('date')}")
        print(f"   Time: {booking_result.get('time')}")
        print(f"   Link: {booking_result.get('link')}")
        print(f"   Verified: {booking_result.get('verified')}")
        
        # Verify random name and description were used
        if booking_result.get('name') == "testmus":
            print("\n⚠️  WARNING: Using 'testmus' instead of random name")
        else:
            print(f"\n✅ Random name used: {booking_result.get('name')}")
        
        print(f"✅ Random description used: {booking_result.get('description')}")
        
        print("\n" + "="*60)
        print("✅ COMPLETE AGENT BOOKING FLOW TEST PASSED!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_full_agent_booking_flow()
    exit(0 if success else 1)
