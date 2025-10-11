from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz

# Configuration
SERVICE_ACCOUNT_FILE = 'kkucapikey.json'
SCOPES = ['http82d967a4c703713740219cbf16b7f044a2c6ccb075a6633ad375d377a201403@group.calendar.google.coms://www.googleapis.com/auth/calendar']
CALENDAR_ID = '2'

# Create credentials
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, 
    scopes=SCOPES
)

# Build the service
service = build('calendar', 'v3', credentials=credentials)

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
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=week_start.isoformat(),
        timeMax=week_end.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
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
    
    created1 = service.events().insert(
        calendarId=CALENDAR_ID,
        body=event1
    ).execute()
    
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
    
    created2 = service.events().insert(
        calendarId=CALENDAR_ID,
        body=event2
    ).execute()
    
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