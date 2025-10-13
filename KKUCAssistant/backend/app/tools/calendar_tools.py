"""
Calendar Tools for Google Calendar Integration
Three tools: fetch available slots, confirm booking, and book appointment
"""
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pytz
import os
import random
from dotenv import load_dotenv

load_dotenv()

# Random names and descriptions for bookings
RANDOM_NAMES = [
    "John Doe", "Jane Smith", "Michael Johnson", "Emily Davis", 
    "David Wilson", "Sarah Brown", "James Taylor", "Emma Anderson",
    "Robert Thomas", "Olivia Martinez", "William Garcia", "Sophia Rodriguez",
    "Daniel Lee", "Isabella White", "Matthew Harris", "Mia Clark"
]

RANDOM_DESCRIPTIONS = [
    "Initial consultation appointment",
    "Follow-up meeting scheduled",
    "Regular check-in session",
    "Quarterly review meeting",
    "Project discussion appointment",
    "Strategy planning session",
    "Team collaboration meeting",
    "Client consultation scheduled",
    "Progress review appointment",
    "Monthly sync-up meeting"
]


class CalendarTools:
    """Tools for interacting with Google Calendar"""
    
    def __init__(self):
        """Initialize Google Calendar service"""
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
        self.danish_tz = pytz.timezone('Europe/Copenhagen')
        
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
        
        # Create credentials and build service
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=self.SCOPES
        )
        self.service = build('calendar', 'v3', credentials=credentials)
    
    def fetch_available_slots(self) -> List[Dict]:
        """
        Tool 1: Fetch available time slots on Tuesday and Wednesday from 10:00-14:00
        Returns list of available 1-hour slots
        """
        print("\n🔍 Tool 1: Fetching available slots...")
        
        # Get next Tuesday and Wednesday
        now_danish = datetime.now(self.danish_tz)
        days_until_tuesday = (1 - now_danish.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_tuesday = (now_danish + timedelta(days=days_until_tuesday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        next_wednesday = next_tuesday + timedelta(days=1)
        
        # Define time range: Tuesday 10:00 to Wednesday 14:00
        start_time = next_tuesday.replace(hour=10, minute=0)
        end_time = next_wednesday.replace(hour=14, minute=0)
        
        # Fetch existing events for both days
        try:
            events_result = self.service.events().list(
                calendarId=self.CALENDAR_ID,
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            booked_events = events_result.get('items', [])
        except HttpError as error:
            print(f"❌ Error fetching events: {error}")
            return []
        
        # Find available 1-hour slots for both Tuesday and Wednesday
        available_slots = []
        days = [
            (next_tuesday, 'Tuesday'),
            (next_wednesday, 'Wednesday')
        ]
        
        for day_date, day_name in days:
            for hour in range(10, 14):  # 10:00, 11:00, 12:00, 13:00
                slot_start = day_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                slot_end = slot_start + timedelta(hours=1)
                
                # Check if slot is available
                is_available = True
                for event in booked_events:
                    event_start = event['start'].get('dateTime', event['start'].get('date'))
                    event_end = event['end'].get('dateTime', event['end'].get('date'))
                    
                    if 'T' in event_start:
                        event_start_dt = datetime.fromisoformat(event_start.replace('Z', '+00:00')).astimezone(self.danish_tz)
                        event_end_dt = datetime.fromisoformat(event_end.replace('Z', '+00:00')).astimezone(self.danish_tz)
                        
                        # Check for overlap
                        if not (slot_end <= event_start_dt or slot_start >= event_end_dt):
                            is_available = False
                            break
                
                if is_available:
                    available_slots.append({
                        'date': slot_start.strftime('%Y-%m-%d'),
                        'day': day_name,
                        'time': slot_start.strftime('%H:%M'),
                        'datetime': slot_start
                    })
        
        print(f"✅ Found {len(available_slots)} available slots (Tuesday & Wednesday)")
        return available_slots
    
    def confirm_booking(self, selected_slot: Dict) -> Dict:
        """
        Tool 2: Lock in the request and prompt user for confirmation
        Returns confirmation details
        """
        print("\n🔒 Tool 2: Confirming booking request...")
        
        confirmation = {
            'status': 'pending_confirmation',
            'slot': selected_slot,
            'message': f"Please confirm booking for {selected_slot['day']}, {selected_slot['date']} at {selected_slot['time']}-{(selected_slot['datetime'] + timedelta(hours=1)).strftime('%H:%M')}"
        }
        
        print(f"✅ Booking locked: {confirmation['message']}")
        return confirmation
    
    def book_appointment(self, slot: Dict, name: str = None) -> Dict:
        """
        Tool 3: Book the appointment via API and verify
        Uses random name and description if not provided
        Returns booking confirmation with verification
        """
        # Generate random name and description if not provided
        if name is None:
            name = random.choice(RANDOM_NAMES)
        description = random.choice(RANDOM_DESCRIPTIONS)
        
        print(f"\n📅 Tool 3: Booking appointment for {name}...")
        print(f"   Description: {description}")
        
        # Handle datetime - it might be a string or datetime object
        slot_start = slot['datetime']
        if isinstance(slot_start, str):
            slot_start = datetime.fromisoformat(slot_start.replace('Z', '+00:00'))
            if slot_start.tzinfo is None:
                slot_start = self.danish_tz.localize(slot_start)
        
        slot_end = slot_start + timedelta(hours=1)
        
        # Create event with random name and description
        event = {
            'summary': name,
            'description': description,
            'start': {
                'dateTime': slot_start.isoformat(),
                'timeZone': 'Europe/Copenhagen',
            },
            'end': {
                'dateTime': slot_end.isoformat(),
                'timeZone': 'Europe/Copenhagen',
            }
        }
        
        # Book via API
        try:
            created_event = self.service.events().insert(
                calendarId=self.CALENDAR_ID,
                body=event
            ).execute()
            
            print(f"✅ API call successful: Event ID {created_event['id']}")
            
            # Double-check by fetching the event
            verification = self.service.events().get(
                calendarId=self.CALENDAR_ID,
                eventId=created_event['id']
            ).execute()
            
            result = {
                'status': 'confirmed',
                'event_id': created_event['id'],
                'name': name,
                'description': description,
                'date': slot['date'],
                'time': slot['time'],
                'link': created_event.get('htmlLink'),
                'verified': True,
                'message': f"✅ Booking confirmed! {name} is scheduled for {slot['day']}, {slot['date']} at {slot['time']}"
            }
            
            print(f"✅ Verification successful: Booking confirmed")
            return result
            
        except HttpError as error:
            print(f"❌ Error booking appointment: {error}")
            return {
                'status': 'failed',
                'error': str(error),
                'message': f"❌ Failed to book appointment: {error}"
            }
