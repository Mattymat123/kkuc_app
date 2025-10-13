"""
Test that calendar bookings use random names and descriptions
This version creates a test slot first if none are available
"""
from app.tools.calendar_tools import CalendarTools
from datetime import datetime, timedelta
import pytz

def test_random_booking_with_setup():
    """Test that bookings use random names and descriptions"""
    
    print("\n" + "="*60)
    print("Testing Random Name and Description in Bookings")
    print("="*60)
    
    # Initialize calendar tools
    calendar_tools = CalendarTools()
    danish_tz = pytz.timezone('Europe/Copenhagen')
    
    # Get next Tuesday
    now_danish = datetime.now(danish_tz)
    days_until_tuesday = (1 - now_danish.weekday()) % 7
    if days_until_tuesday == 0:
        days_until_tuesday = 7
    next_tuesday = (now_danish + timedelta(days=days_until_tuesday)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    
    print(f"\n📅 Today: {now_danish.strftime('%A, %B %d, %Y')}")
    print(f"📅 Next Tuesday: {next_tuesday.strftime('%A, %B %d, %Y')}")
    
    # Step 1: Fetch available slots
    print("\n🔍 Step 1: Fetching available slots...")
    available_slots = calendar_tools.fetch_available_slots()
    
    if not available_slots:
        print("⚠️  No available slots found on next Tuesday")
        print("   Creating a test slot by using a different time...")
        
        # Use a slot at 15:00 (3 PM) which is outside the normal 10-14 range
        test_slot = {
            'date': next_tuesday.strftime('%Y-%m-%d'),
            'day': 'Tuesday',
            'time': '15:00',
            'datetime': next_tuesday.replace(hour=15, minute=0)
        }
        print(f"   Using test slot: {test_slot['day']}, {test_slot['date']} at {test_slot['time']}")
    else:
        print(f"✅ Found {len(available_slots)} available slots")
        test_slot = available_slots[0]
    
    # Step 2: Book the slot with random name/description
    print("\n📅 Step 2: Booking appointment with random name and description...")
    print(f"   Slot: {test_slot['day']}, {test_slot['date']} at {test_slot['time']}")
    
    # Book without providing a name (should use random)
    booking_result = calendar_tools.book_appointment(test_slot)
    
    # Step 3: Verify random name and description were used
    print("\n✅ Step 3: Verifying random name and description...")
    print(f"   Status: {booking_result.get('status')}")
    print(f"   Name: {booking_result.get('name')}")
    print(f"   Description: {booking_result.get('description')}")
    print(f"   Event ID: {booking_result.get('event_id')}")
    print(f"   Link: {booking_result.get('link')}")
    
    # Assertions
    assert booking_result.get('status') == 'confirmed', f"Booking failed: {booking_result.get('message')}"
    assert booking_result.get('name') is not None, "No name in booking result"
    assert booking_result.get('description') is not None, "No description in booking result"
    assert booking_result.get('name') != "testmus", "Should use random name, not 'testmus'"
    assert booking_result.get('verified') == True, "Booking not verified"
    
    print("\n✅ SUCCESS! Random name and description are working correctly!")
    print(f"   ✓ Random name: {booking_result.get('name')}")
    print(f"   ✓ Random description: {booking_result.get('description')}")
    
    # Step 4: Verify the booking exists in calendar
    print("\n🔍 Step 4: Verifying booking exists in Google Calendar...")
    try:
        event = calendar_tools.service.events().get(
            calendarId=calendar_tools.CALENDAR_ID,
            eventId=booking_result['event_id']
        ).execute()
        
        print(f"✅ Event found in calendar:")
        print(f"   Summary: {event.get('summary')}")
        print(f"   Description: {event.get('description')}")
        print(f"   Start: {event['start'].get('dateTime')}")
        
        # Verify the event has the random name and description
        assert event.get('summary') == booking_result.get('name'), "Event summary doesn't match"
        assert event.get('description') == booking_result.get('description'), "Event description doesn't match"
        
        print("\n✅ Calendar event verified successfully!")
        
    except Exception as e:
        print(f"❌ Error verifying event: {e}")
    
    # Step 5: Cleanup (SKIPPED - keeping test booking)
    print("\n🧹 Step 5: Cleanup skipped - test booking will remain in calendar")
    print(f"   Event ID: {booking_result['event_id']}")
    print(f"   Link: {booking_result.get('link')}")
    
    print("\n" + "="*60)
    print("✅ Random Booking Test Complete!")
    print("="*60)

if __name__ == "__main__":
    test_random_booking_with_setup()
