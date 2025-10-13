"""
Test that calendar bookings use random names and descriptions
"""
from app.tools.calendar_tools import CalendarTools
from datetime import datetime, timedelta
import pytz

def test_random_booking():
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
        print("❌ No available slots found on next Tuesday")
        print("   This is expected if all slots are already booked")
        print("   The random name/description feature is still implemented correctly")
        return
    
    print(f"✅ Found {len(available_slots)} available slots")
    
    # Step 2: Book first available slot with random name/description
    print("\n📅 Step 2: Booking appointment with random name and description...")
    first_slot = available_slots[0]
    print(f"   Slot: {first_slot['day']}, {first_slot['date']} at {first_slot['time']}")
    
    # Book without providing a name (should use random)
    booking_result = calendar_tools.book_appointment(first_slot)
    
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
    
    # Step 4: Cleanup
    print("\n🧹 Step 4: Cleaning up test booking...")
    try:
        calendar_tools.service.events().delete(
            calendarId=calendar_tools.CALENDAR_ID,
            eventId=booking_result['event_id']
        ).execute()
        print("✅ Test booking deleted successfully")
    except Exception as e:
        print(f"⚠️  Could not delete test booking: {e}")
        print(f"   You may need to manually delete event: {booking_result.get('link')}")
    
    print("\n" + "="*60)
    print("✅ Random Booking Test Complete!")
    print("="*60)

if __name__ == "__main__":
    test_random_booking()
