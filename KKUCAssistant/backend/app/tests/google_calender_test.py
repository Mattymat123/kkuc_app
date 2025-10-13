from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
import pytz
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# Configuration from environment variables
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID', 'primary')

# Build service account info from environment variables
service_account_info = {
    "type": os.getenv('GOOGLE_CALENDAR_TYPE'),
    "project_id": os.getenv('GOOGLE_CALENDAR_PROJECT_ID'),
    "private_key_id": os.getenv('GOOGLE_CALENDAR_PRIVATE_KEY_ID'),
    "private_key": os.getenv('GOOGLE_CALENDAR_PRIVATE_KEY'),
    "client_email": os.getenv('GOOGLE_CALENDAR_CLIENT_EMAIL'),
    "client_id": os.getenv('GOOGLE_CALENDAR_CLIENT_ID'),
    "auth_uri": os.getenv('GOOGLE_CALENDAR_AUTH_URI'),
    "token_uri": os.getenv('GOOGLE_CALENDAR_TOKEN_URI'),
    "auth_provider_x509_cert_url": os.getenv('GOOGLE_CALENDAR_AUTH_PROVIDER_CERT_URL'),
    "client_x509_cert_url": os.getenv('GOOGLE_CALENDAR_CLIENT_CERT_URL'),
    "universe_domain": os.getenv('GOOGLE_CALENDAR_UNIVERSE_DOMAIN')
}

# Validate required environment variables
required_vars = ['GOOGLE_CALENDAR_CLIENT_EMAIL', 'GOOGLE_CALENDAR_PRIVATE_KEY', 'GOOGLE_CALENDAR_PROJECT_ID']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Create credentials from service account info
try:
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=SCOPES
    )
    print("✅ Credentials loaded successfully from environment variables")
except Exception as e:
    print(f"❌ Error loading credentials: {e}")
    raise

# Build the service
try:
    service = build('calendar', 'v3', credentials=credentials)
    print("✅ Calendar service built successfully")
    print(f"📧 Service account email: {os.getenv('GOOGLE_CALENDAR_CLIENT_EMAIL')}")
    print(f"📅 Using calendar: {CALENDAR_ID}")
except Exception as e:
    print(f"❌ Error building service: {e}")
    raise

# List available calendars to help debug
print("\n🔍 Listing accessible calendars...")
try:
    calendar_list = service.calendarList().list().execute()
    calendars = calendar_list.get('items', [])
    if calendars:
        print(f"✅ Found {len(calendars)} accessible calendar(s):")
        for cal in calendars:
            print(f"   • {cal.get('summary', 'No name')} (ID: {cal['id']})")
    else:
        print("⚠️ No calendars found. You may need to:")
        print(f"   1. Share your Google Calendar with: {os.getenv('GOOGLE_CALENDAR_CLIENT_EMAIL')}")
        print("   2. Or create a calendar in the service account's Google Calendar")
except HttpError as error:
    print(f"⚠️ Could not list calendars: {error}")
print()

danish_tz = pytz.timezone('Europe/Copenhagen')
now_danish = datetime.now(danish_tz)

# Get next Monday
days_until_monday = (7 - now_danish.weekday()) % 7
if days_until_monday == 0:
    days_until_monday = 7
next_monday = (now_danish + timedelta(days=days_until_monday)).replace(hour=0, minute=0, second=0, microsecond=0)

week_start = next_monday
week_end = next_monday + timedelta(days=3)

# Function to get available slots
def get_available_slots():
    try:
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=week_start.isoformat(),
            timeMax=week_end.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
    except HttpError as error:
        if error.resp.status == 404:
            print(f"❌ Calendar not found!")
            print(f"\n💡 SOLUTION:")
            print(f"   1. Go to your Google Calendar (calendar.google.com)")
            print(f"   2. Find the calendar you want to use")
            print(f"   3. Click Settings (gear icon) → Settings")
            print(f"   4. Select your calendar from the left sidebar")
            print(f"   5. Scroll to 'Share with specific people'")
            print(f"   6. Click '+ Add people'")
            print(f"   7. Add: {os.getenv('GOOGLE_CALENDAR_CLIENT_EMAIL')}")
            print(f"   8. Give it 'Make changes to events' permission")
            print(f"   9. Update GOOGLE_CALENDAR_ID in your .env file with your calendar's ID")
            print(f"      (Found in Settings → Integrate calendar → Calendar ID)")
        print(f"\n❌ Error details: {error}")
        raise
    
    booked_events = events_result.get('items', [])
    
    def is_slot_available(slot_start, slot_end, booked_events):
        for event in booked_events:
            event_start = event['start'].get('dateTime', event['start'].get('date'))
            event_end = event['end'].get('dateTime', event['end'].get('date'))
            
            if 'T' in event_start:
                event_start_dt = datetime.fromisoformat(event_start.replace('Z', '+00:00')).astimezone(danish_tz)
                event_end_dt = datetime.fromisoformat(event_end.replace('Z', '+00:00')).astimezone(danish_tz)
                
                if not (slot_end <= event_start_dt or slot_start >= event_end_dt):
                    return False
        return True
    
    available_slots = []
    day_names = ['Monday', 'Tuesday', 'Wednesday']
    
    for day_offset in range(3):
        current_day = next_monday + timedelta(days=day_offset)
        day_name = day_names[day_offset]
        
        for hour in range(10, 14):
            slot_start = current_day.replace(hour=hour, minute=0, second=0, microsecond=0)
            slot_end = slot_start + timedelta(hours=1)
            
            if is_slot_available(slot_start, slot_end, booked_events):
                available_slots.append({
                    'day': day_name,
                    'date': slot_start.strftime('%B %d'),
                    'time': slot_start.strftime('%H:%M'),
                    'datetime': slot_start
                })
    
    return available_slots

# Function to display slots
def display_slots(slots, title):
    print(f"\n{title}")
    print("=" * 60)
    if slots:
        print(f"✅ Found {len(slots)} available 1-hour slots:\n")
        current_day = None
        for slot in slots:
            if slot['day'] != current_day:
                print(f"\n📅 {slot['day']}, {slot['date']}:")
                current_day = slot['day']
            print(f"   • {slot['time']} - {(slot['datetime'] + timedelta(hours=1)).strftime('%H:%M')}")
    else:
        print("❌ No available slots found.")
    print("=" * 60)

# ============================================
# STEP 1: Check available slots BEFORE booking
# ============================================
print("\n🔍 STEP 1: Checking available slots BEFORE booking...")
available_before = get_available_slots()
display_slots(available_before, "AVAILABLE SLOTS (BEFORE BOOKING)")

# ============================================
# STEP 2: Book 2 appointments
# ============================================
print("\n\n📅 STEP 2: Booking 2 test appointments...")
print("=" * 60)

if len(available_before) < 2:
    print("❌ Not enough available slots to book 2 appointments!")
else:
    # Book first appointment
    slot1 = available_before[0]
    start1 = slot1['datetime']
    end1 = start1 + timedelta(hours=1)
    
    event1 = {
        'summary': 'TEST BOOKING #1',
        'description': 'First test appointment',
        'start': {
            'dateTime': start1.isoformat(),
            'timeZone': 'Europe/Copenhagen',
        },
        'end': {
            'dateTime': end1.isoformat(),
            'timeZone': 'Europe/Copenhagen',
        }
    }
    
    try:
        created1 = service.events().insert(
            calendarId=CALENDAR_ID,
            body=event1
        ).execute()
    except HttpError as error:
        print(f"❌ Error creating appointment #1: {error}")
        raise
    
    print(f"\n✅ Appointment #1 booked!")
    print(f"   {slot1['day']}, {slot1['date']} at {slot1['time']}")
    print(f"   Link: {created1.get('htmlLink')}")
    
    # Book second appointment
    slot2 = available_before[1]
    start2 = slot2['datetime']
    end2 = start2 + timedelta(hours=1)
    
    event2 = {
        'summary': 'TEST BOOKING #2',
        'description': 'Second test appointment',
        'start': {
            'dateTime': start2.isoformat(),
            'timeZone': 'Europe/Copenhagen',
        },
        'end': {
            'dateTime': end2.isoformat(),
            'timeZone': 'Europe/Copenhagen',
        }
    }
    
    try:
        created2 = service.events().insert(
            calendarId=CALENDAR_ID,
            body=event2
        ).execute()
    except HttpError as error:
        print(f"❌ Error creating appointment #2: {error}")
        raise
    
    print(f"\n✅ Appointment #2 booked!")
    print(f"   {slot2['day']}, {slot2['date']} at {slot2['time']}")
    print(f"   Link: {created2.get('htmlLink')}")
    
    print("\n" + "=" * 60)
    
    # ============================================
    # STEP 3: Check available slots AFTER booking
    # ============================================
    print("\n\n🔍 STEP 3: Checking available slots AFTER booking...")
    available_after = get_available_slots()
    display_slots(available_after, "AVAILABLE SLOTS (AFTER BOOKING)")
    
    # ============================================
    # STEP 4: Show the difference
    # ============================================
    print("\n\n📊 STEP 4: Summary of changes...")
    print("=" * 60)
    print(f"Slots before: {len(available_before)}")
    print(f"Slots booked: 2")
    print(f"Slots after:  {len(available_after)}")
    print(f"Difference:   {len(available_before) - len(available_after)} slots removed")
    
    if len(available_before) - len(available_after) == 2:
        print("\n✅ SUCCESS! Both appointments are now blocking those time slots!")
    else:
        print("\n⚠️ Warning: Expected 2 fewer slots, but difference is different.")
    
    print("=" * 60)
    
    print("\n\n👀 CHECK YOUR GOOGLE CALENDAR NOW!")
    print(f"You should see 'TEST BOOKING #1' and 'TEST BOOKING #2' in your calendar.")
    print(f"Calendar: {CALENDAR_ID[:20]}...")
    
    # ============================================
    # STEP 5: Cleanup option
    # ============================================
    print("\n\n🧹 CLEANUP: Delete test appointments?")
    print("=" * 60)
    cleanup = input("Delete the test appointments? (yes/no): ").strip().lower()
    
    if cleanup == 'yes':
        try:
            service.events().delete(calendarId=CALENDAR_ID, eventId=created1['id']).execute()
            print(f"✅ Deleted appointment #1")
        except HttpError as error:
            print(f"❌ Error deleting appointment #1: {error}")
        
        try:
            service.events().delete(calendarId=CALENDAR_ID, eventId=created2['id']).execute()
            print(f"✅ Deleted appointment #2")
        except HttpError as error:
            print(f"❌ Error deleting appointment #2: {error}")
        
        print("\n✅ Cleanup complete!")
    else:
        print("⏭️ Skipping cleanup. Appointments remain in calendar.")
    
    print("=" * 60)
