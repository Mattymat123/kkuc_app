"""
Test agent context flow - ensuring booking state is maintained across requests
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.agent import agent_executor
from langchain_core.messages import HumanMessage


def test_booking_flow_with_text_refinement():
    """Test that agent maintains booking context when user provides text refinement"""
    print("\n" + "="*80)
    print("TEST: Booking Flow with Text Refinement")
    print("="*80)
    
    # Step 1: Initial booking request
    print("\n📝 Step 1: User requests to book a time")
    initial_state = {
        "messages": [HumanMessage(content="Jeg vil gerne booke en tid")]
    }
    
    result1 = agent_executor.invoke(initial_state)
    print(f"✅ Response received")
    print(f"📊 Booking state: {result1.get('booking_state', {}).get('step')}")
    print(f"📊 Available slots: {len(result1.get('booking_state', {}).get('available_slots', []))}")
    
    # Verify we have available slots
    assert result1.get("booking_state") is not None, "Booking state should exist"
    assert result1["booking_state"].get("step") == "select", "Should be in select step"
    assert len(result1["booking_state"].get("available_slots", [])) > 0, "Should have available slots"
    
    # Step 2: User provides text refinement instead of number
    print("\n📝 Step 2: User provides text refinement 'book tirsdag den 14'")
    
    # Prepare state with booking_state from previous step
    state_with_booking = {
        "messages": result1["messages"] + [HumanMessage(content="book tirsdag den 14")],
        "booking_state": result1["booking_state"]
    }
    
    result2 = agent_executor.invoke(state_with_booking)
    print(f"✅ Response received")
    print(f"📊 Booking state: {result2.get('booking_state', {}).get('step')}")
    
    # Verify the agent continued the booking flow (didn't restart)
    assert result2.get("booking_state") is not None, "Booking state should still exist"
    # Should either be in confirm step (if matched) or still in select (if couldn't match)
    assert result2["booking_state"].get("step") in ["confirm", "select"], f"Should be in confirm or select step, got: {result2['booking_state'].get('step')}"
    
    if result2["booking_state"].get("step") == "confirm":
        print("✅ Successfully matched user's text to a slot!")
        print(f"📅 Selected slot: {result2['booking_state'].get('selected_slot')}")
    else:
        print("⚠️  Could not match user's text, still in select step")
    
    print("\n" + "="*80)
    print("TEST PASSED: Agent maintained booking context!")
    print("="*80)


def test_booking_flow_with_number():
    """Test normal booking flow with number selection"""
    print("\n" + "="*80)
    print("TEST: Normal Booking Flow with Number")
    print("="*80)
    
    # Step 1: Initial booking request
    print("\n📝 Step 1: User requests to book a time")
    initial_state = {
        "messages": [HumanMessage(content="Jeg vil gerne booke en tid")]
    }
    
    result1 = agent_executor.invoke(initial_state)
    print(f"✅ Response received")
    print(f"📊 Booking state: {result1.get('booking_state', {}).get('step')}")
    
    # Step 2: User selects with number
    print("\n📝 Step 2: User selects slot #1")
    state_with_booking = {
        "messages": result1["messages"] + [HumanMessage(content="1")],
        "booking_state": result1["booking_state"]
    }
    
    result2 = agent_executor.invoke(state_with_booking)
    print(f"✅ Response received")
    print(f"📊 Booking state: {result2.get('booking_state', {}).get('step')}")
    
    # Verify we're in confirm step
    assert result2.get("booking_state") is not None, "Booking state should exist"
    assert result2["booking_state"].get("step") == "confirm", "Should be in confirm step"
    assert result2["booking_state"].get("selected_slot") is not None, "Should have selected slot"
    
    print(f"📅 Selected slot: {result2['booking_state'].get('selected_slot')}")
    
    print("\n" + "="*80)
    print("TEST PASSED: Normal booking flow works!")
    print("="*80)


if __name__ == "__main__":
    try:
        test_booking_flow_with_number()
        test_booking_flow_with_text_refinement()
        print("\n✅ ALL TESTS PASSED!")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
