"""
Complete end-to-end test of the calendar booking flow
Tests the full flow: fetch slots -> select slot -> confirm -> verify booking
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://0.0.0.0:8000/chat"

def test_complete_booking_flow():
    """Test the complete booking flow with proper state management"""
    
    print("\n" + "="*60)
    print("Testing COMPLETE Calendar Booking Flow")
    print("="*60)
    
    # Step 1: Initial booking request - fetch available slots
    print("\n📅 Step 1: Request to book a time")
    response1 = requests.post(
        BASE_URL,
        json={
            "messages": [
                {"role": "user", "content": "Jeg vil gerne booke en tid"}
            ]
        },
        stream=True
    )
    
    print(f"Status: {response1.status_code}")
    
    # Collect the response and extract booking_state
    response1_text = ""
    booking_state_1 = None
    
    for line in response1.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith('0:'):
                # Extract the content
                content = json.loads(decoded[2:])
                response1_text += content
                print(content, end='', flush=True)
            elif decoded.startswith('2:'):
                # Extract booking_state
                state_data = json.loads(decoded[2:])
                if isinstance(state_data, list) and len(state_data) > 0:
                    booking_state_1 = state_data[0]
    
    print(f"\n\n✅ Response 1 received")
    print(f"📊 Booking state received: {booking_state_1 is not None}")
    if booking_state_1:
        print(f"   Step: {booking_state_1.get('step')}")
        print(f"   Available slots: {len(booking_state_1.get('available_slots', []))}")
        
        # Print the available slots
        if booking_state_1.get('available_slots'):
            print("\n📋 Available slots:")
            for i, slot in enumerate(booking_state_1['available_slots'], 1):
                print(f"   {i}. {slot['day']}, {slot['date']} kl. {slot['time']}")
    
    # Verify we got slots
    assert booking_state_1 is not None, "No booking_state received in step 1"
    assert booking_state_1.get('step') == 'select', f"Expected step 'select', got '{booking_state_1.get('step')}'"
    assert len(booking_state_1.get('available_slots', [])) > 0, "No available slots found"
    
    initial_slot_count = len(booking_state_1['available_slots'])
    print(f"\n✅ Initial available slots: {initial_slot_count}")
    
    # Step 2: Select slot #1
    print("\n\n📅 Step 2: Select slot #1")
    response2 = requests.post(
        BASE_URL,
        json={
            "messages": [
                {"role": "user", "content": "Jeg vil gerne booke en tid"},
                {"role": "assistant", "content": response1_text},
                {"role": "user", "content": "1"}
            ],
            "booking_state": booking_state_1  # Pass the actual booking_state from step 1
        },
        stream=True
    )
    
    print(f"Status: {response2.status_code}")
    
    # Collect the response
    response2_text = ""
    booking_state_2 = None
    
    for line in response2.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith('0:'):
                content = json.loads(decoded[2:])
                response2_text += content
                print(content, end='', flush=True)
            elif decoded.startswith('2:'):
                state_data = json.loads(decoded[2:])
                if isinstance(state_data, list) and len(state_data) > 0:
                    booking_state_2 = state_data[0]
    
    print(f"\n\n✅ Response 2 received")
    print(f"📊 Booking state received: {booking_state_2 is not None}")
    if booking_state_2:
        print(f"   Step: {booking_state_2.get('step')}")
        print(f"   Selected slot: {booking_state_2.get('selected_slot')}")
    
    # Verify we selected a slot
    assert booking_state_2 is not None, "No booking_state received in step 2"
    assert booking_state_2.get('step') == 'confirm', f"Expected step 'confirm', got '{booking_state_2.get('step')}'"
    assert booking_state_2.get('selected_slot') is not None, "No slot was selected"
    
    selected_slot = booking_state_2['selected_slot']
    print(f"\n✅ Selected slot: {selected_slot['day']}, {selected_slot['date']} kl. {selected_slot['time']}")
    
    # Step 3: Confirm booking
    print("\n\n📅 Step 3: Confirm booking")
    response3 = requests.post(
        BASE_URL,
        json={
            "messages": [
                {"role": "user", "content": "Jeg vil gerne booke en tid"},
                {"role": "assistant", "content": response1_text},
                {"role": "user", "content": "1"},
                {"role": "assistant", "content": response2_text},
                {"role": "user", "content": "ja"}
            ],
            "booking_state": booking_state_2  # Pass the booking_state from step 2
        },
        stream=True
    )
    
    print(f"Status: {response3.status_code}")
    
    # Collect the response
    response3_text = ""
    booking_state_3 = None
    
    for line in response3.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith('0:'):
                content = json.loads(decoded[2:])
                response3_text += content
                print(content, end='', flush=True)
            elif decoded.startswith('2:'):
                state_data = json.loads(decoded[2:])
                if isinstance(state_data, list) and len(state_data) > 0:
                    booking_state_3 = state_data[0]
    
    print(f"\n\n✅ Response 3 received")
    print(f"📊 Booking state received: {booking_state_3 is not None}")
    if booking_state_3:
        print(f"   Step: {booking_state_3.get('step')}")
        print(f"   Booking result: {booking_state_3.get('booking_result')}")
    
    # Verify booking was completed
    assert booking_state_3 is not None, "No booking_state received in step 3"
    assert booking_state_3.get('step') == 'complete', f"Expected step 'complete', got '{booking_state_3.get('step')}'"
    assert booking_state_3.get('booking_result') is not None, "No booking result received"
    
    booking_result = booking_state_3['booking_result']
    print(f"\n✅ Booking completed successfully!")
    print(f"   Date: {booking_result.get('date')}")
    print(f"   Time: {booking_result.get('time')}")
    print(f"   Name: {booking_result.get('name')}")
    print(f"   Description: {booking_result.get('description')}")
    print(f"   Event ID: {booking_result.get('event_id')}")
    print(f"   Link: {booking_result.get('link')}")
    
    # Verify that random name and description were used
    assert booking_result.get('name') is not None, "No name in booking result"
    assert booking_result.get('description') is not None, "No description in booking result"
    assert booking_result.get('name') != "testmus", "Should use random name, not 'testmus'"
    print(f"\n✅ Random name and description verified!")
    print(f"   Random name used: {booking_result.get('name')}")
    print(f"   Random description used: {booking_result.get('description')}")
    
    # Step 4: Verify one less slot is available
    print("\n\n📅 Step 4: Verify booking by checking available slots again")
    response4 = requests.post(
        BASE_URL,
        json={
            "messages": [
                {"role": "user", "content": "Vis mig ledige tider"}
            ]
        },
        stream=True
    )
    
    print(f"Status: {response4.status_code}")
    
    # Collect the response
    response4_text = ""
    booking_state_4 = None
    
    for line in response4.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith('0:'):
                content = json.loads(decoded[2:])
                response4_text += content
                print(content, end='', flush=True)
            elif decoded.startswith('2:'):
                state_data = json.loads(decoded[2:])
                if isinstance(state_data, list) and len(state_data) > 0:
                    booking_state_4 = state_data[0]
    
    print(f"\n\n✅ Response 4 received")
    if booking_state_4 and booking_state_4.get('available_slots'):
        final_slot_count = len(booking_state_4['available_slots'])
        print(f"\n📊 Slot count comparison:")
        print(f"   Initial slots: {initial_slot_count}")
        print(f"   Final slots: {final_slot_count}")
        print(f"   Difference: {initial_slot_count - final_slot_count}")
        
        if final_slot_count < initial_slot_count:
            print(f"\n✅ SUCCESS! One slot was booked (slots reduced from {initial_slot_count} to {final_slot_count})")
        else:
            print(f"\n⚠️  WARNING: Slot count did not decrease (still {final_slot_count} slots)")
        
        # Print remaining slots
        print("\n📋 Remaining available slots:")
        for i, slot in enumerate(booking_state_4['available_slots'], 1):
            print(f"   {i}. {slot['day']}, {slot['date']} kl. {slot['time']}")
    
    print("\n" + "="*60)
    print("✅ Complete Booking Flow Test Finished!")
    print("="*60)

if __name__ == "__main__":
    test_complete_booking_flow()
