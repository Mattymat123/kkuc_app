"""
Test the calendar booking flow with booking_state persistence
"""
import requests
import json

BASE_URL = "http://0.0.0.0:8000/chat"

def test_booking_flow():
    """Test the complete booking flow"""
    
    print("\n" + "="*60)
    print("Testing Calendar Booking Flow")
    print("="*60)
    
    # Step 1: Initial booking request
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
    
    # Collect the response
    response1_text = ""
    for line in response1.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith('0:'):
                # Extract the content
                content = json.loads(decoded[2:])
                response1_text += content
                print(content, end='', flush=True)
    
    print(f"\n\n✅ Response 1 received")
    print(f"Response contains 'Vælg': {('Vælg' in response1_text or 'vælg' in response1_text)}")
    
    # Step 2: Select a slot (with booking_state)
    print("\n\n📅 Step 2: Select slot #2")
    response2 = requests.post(
        BASE_URL,
        json={
            "messages": [
                {"role": "user", "content": "Jeg vil gerne booke en tid"},
                {"role": "assistant", "content": response1_text},
                {"role": "user", "content": "2"}
            ],
            "booking_state": {
                "step": "select",
                "available_slots": []  # Would be populated in real scenario
            }
        },
        stream=True
    )
    
    print(f"Status: {response2.status_code}")
    
    # Collect the response
    response2_text = ""
    for line in response2.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith('0:'):
                content = json.loads(decoded[2:])
                response2_text += content
                print(content, end='', flush=True)
    
    print(f"\n\n✅ Response 2 received")
    print(f"Response contains 'Bekræft': {('Bekræft' in response2_text or 'bekræft' in response2_text)}")
    
    # Step 3: Confirm booking
    print("\n\n📅 Step 3: Confirm booking")
    response3 = requests.post(
        BASE_URL,
        json={
            "messages": [
                {"role": "user", "content": "Jeg vil gerne booke en tid"},
                {"role": "assistant", "content": response1_text},
                {"role": "user", "content": "2"},
                {"role": "assistant", "content": response2_text},
                {"role": "user", "content": "ja"}
            ],
            "booking_state": {
                "step": "confirm",
                "selected_slot": {}  # Would be populated in real scenario
            }
        },
        stream=True
    )
    
    print(f"Status: {response3.status_code}")
    
    # Collect the response
    response3_text = ""
    for line in response3.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith('0:'):
                content = json.loads(decoded[2:])
                response3_text += content
                print(content, end='', flush=True)
    
    print(f"\n\n✅ Response 3 received")
    print(f"Response contains 'booket': {('booket' in response3_text or 'Booket' in response3_text)}")
    
    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60)

if __name__ == "__main__":
    test_booking_flow()
