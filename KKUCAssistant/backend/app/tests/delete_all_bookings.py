"""
Script to delete all bookings from the test Google Calendar
"""
from app.tools.calendar_tools import CalendarTools
from datetime import datetime, timedelta
import pytz

def delete_all_bookings():
    """Delete all events from the calendar"""
    
    print("\n" + "="*60)
    print("Deleting All Bookings from Test Calendar")
    print("="*60)
    
    # Initialize calendar tools
    calendar_tools = CalendarTools()
    danish_tz = pytz.timezone('Europe/Copenhagen')
    
    # Get a wide time range to catch all events
    # Start from 30 days ago to 90 days in the future
    now_danish = datetime.now(danish_tz)
    start_time = (now_danish - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = (now_danish + timedelta(days=90)).replace(hour=23, minute=59, second=59, microsecond=0)
    
    print(f"\n📅 Searching for events from {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}")
    
    try:
        # Fetch all events in the time range
        events_result = calendar_tools.service.events().list(
            calendarId=calendar_tools.CALENDAR_ID,
            timeMin=start_time.isoformat(),
            timeMax=end_time.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            print("\n✅ No events found in calendar. Calendar is already empty!")
            return
        
        print(f"\n🔍 Found {len(events)} event(s) to delete:")
        
        # List all events
        for i, event in enumerate(events, 1):
            summary = event.get('summary', 'No title')
            start = event['start'].get('dateTime', event['start'].get('date'))
            event_id = event['id']
            print(f"   {i}. {summary} - {start} (ID: {event_id})")
        
        # Delete all events
        print(f"\n🗑️  Deleting {len(events)} event(s)...")
        deleted_count = 0
        failed_count = 0
        
        for event in events:
            try:
                calendar_tools.service.events().delete(
                    calendarId=calendar_tools.CALENDAR_ID,
                    eventId=event['id']
                ).execute()
                deleted_count += 1
                print(f"   ✅ Deleted: {event.get('summary', 'No title')}")
            except Exception as e:
                failed_count += 1
                print(f"   ❌ Failed to delete {event.get('summary', 'No title')}: {e}")
        
        print(f"\n" + "="*60)
        print(f"✅ Deletion Complete!")
        print(f"   Successfully deleted: {deleted_count}")
        if failed_count > 0:
            print(f"   Failed to delete: {failed_count}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error fetching or deleting events: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    delete_all_bookings()
