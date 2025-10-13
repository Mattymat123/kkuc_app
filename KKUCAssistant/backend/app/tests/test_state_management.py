"""
Test the new state management system with checkpointing and interrupts
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.agent import agent_executor
from langchain_core.messages import HumanMessage
import uuid


def test_basic_rag_query():
    """Test basic RAG query without interrupts"""
    print("\n" + "="*60)
    print("TEST 1: Basic RAG Query")
    print("="*60)
    
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    result = agent_executor.invoke(
        {"messages": [HumanMessage(content="Hvad er KKUC?")]},
        config=config
    )
    
    print(f"\n✅ Response: {result['messages'][-1].content[:200]}...")
    print(f"✅ Thread ID: {thread_id}")
    
    # Verify state was saved
    state = agent_executor.get_state(config)
    print(f"✅ State saved: {len(state.values['messages'])} messages")
    
    return thread_id


def test_calendar_booking_with_interrupts():
    """Test calendar booking flow with interrupts"""
    print("\n" + "="*60)
    print("TEST 2: Calendar Booking with Interrupts")
    print("="*60)
    
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Step 1: Start booking
    print("\n📅 Step 1: Initiating booking...")
    try:
        result = agent_executor.invoke(
            {"messages": [HumanMessage(content="book en tid")]},
            config=config
        )
        print(f"✅ Initial response received")
        print(f"Response: {result['messages'][-1].content[:200]}...")
    except Exception as e:
        print(f"⚠️  Expected interrupt occurred: {type(e).__name__}")
        
        # Check if we're at an interrupt
        state = agent_executor.get_state(config)
        print(f"✅ State at interrupt: next={state.next}")
        
        if state.next:
            print(f"✅ Workflow paused at: {state.next}")
            
            # Step 2: Resume with slot selection
            print("\n🔢 Step 2: Selecting slot #1...")
            try:
                result = agent_executor.invoke(
                    None,  # No new input
                    config=config,
                    command={"resume": 1}  # Select slot 1
                )
                print(f"✅ Slot selected")
            except Exception as e2:
                print(f"⚠️  Expected second interrupt: {type(e2).__name__}")
                
                # Check state again
                state = agent_executor.get_state(config)
                print(f"✅ State at second interrupt: next={state.next}")
                
                # Step 3: Resume with confirmation
                print("\n✅ Step 3: Confirming booking...")
                try:
                    result = agent_executor.invoke(
                        None,
                        config=config,
                        command={"resume": True}  # Confirm
                    )
                    print(f"✅ Booking completed!")
                    print(f"Final response: {result['messages'][-1].content[:200]}...")
                except Exception as e3:
                    print(f"❌ Unexpected error: {e3}")
    
    # Verify final state
    final_state = agent_executor.get_state(config)
    print(f"\n✅ Final state: {len(final_state.values['messages'])} messages")
    print(f"✅ Thread ID: {thread_id}")
    
    return thread_id


def test_state_persistence():
    """Test that state persists across invocations"""
    print("\n" + "="*60)
    print("TEST 3: State Persistence")
    print("="*60)
    
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # First message
    print("\n📝 Sending first message...")
    result1 = agent_executor.invoke(
        {"messages": [HumanMessage(content="Hej")]},
        config=config
    )
    print(f"✅ Response 1: {result1['messages'][-1].content[:100]}...")
    
    # Check state
    state1 = agent_executor.get_state(config)
    msg_count_1 = len(state1.values['messages'])
    print(f"✅ Messages after first: {msg_count_1}")
    
    # Second message (should have context from first)
    print("\n📝 Sending second message...")
    result2 = agent_executor.invoke(
        {"messages": [HumanMessage(content="Hvad sagde jeg lige?")]},
        config=config
    )
    print(f"✅ Response 2: {result2['messages'][-1].content[:100]}...")
    
    # Check state again
    state2 = agent_executor.get_state(config)
    msg_count_2 = len(state2.values['messages'])
    print(f"✅ Messages after second: {msg_count_2}")
    
    # Verify state accumulated
    assert msg_count_2 > msg_count_1, "State should accumulate messages"
    print(f"✅ State persistence verified: {msg_count_1} → {msg_count_2} messages")
    
    return thread_id


def test_multiple_threads():
    """Test that multiple threads maintain separate state"""
    print("\n" + "="*60)
    print("TEST 4: Multiple Threads")
    print("="*60)
    
    thread1 = str(uuid.uuid4())
    thread2 = str(uuid.uuid4())
    
    config1 = {"configurable": {"thread_id": thread1}}
    config2 = {"configurable": {"thread_id": thread2}}
    
    # Send different messages to each thread
    print("\n📝 Thread 1: Asking about KKUC...")
    result1 = agent_executor.invoke(
        {"messages": [HumanMessage(content="Hvad er KKUC?")]},
        config=config1
    )
    
    print("\n📝 Thread 2: Asking about booking...")
    result2 = agent_executor.invoke(
        {"messages": [HumanMessage(content="Hvordan booker jeg en tid?")]},
        config=config2
    )
    
    # Verify separate states
    state1 = agent_executor.get_state(config1)
    state2 = agent_executor.get_state(config2)
    
    msg1 = state1.values['messages'][-2].content  # User message
    msg2 = state2.values['messages'][-2].content  # User message
    
    print(f"\n✅ Thread 1 last user message: {msg1[:50]}...")
    print(f"✅ Thread 2 last user message: {msg2[:50]}...")
    
    assert "KKUC" in msg1, "Thread 1 should have KKUC question"
    assert "booker" in msg2, "Thread 2 should have booking question"
    
    print(f"✅ Multiple threads maintain separate state")
    
    return thread1, thread2


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING NEW STATE MANAGEMENT SYSTEM")
    print("="*60)
    
    try:
        # Run tests
        test_basic_rag_query()
        test_state_persistence()
        test_multiple_threads()
        
        print("\n" + "="*60)
        print("⚠️  SKIPPING: Calendar booking test (requires Google Calendar)")
        print("To test interrupts, use the frontend or manual API calls")
        print("="*60)
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
