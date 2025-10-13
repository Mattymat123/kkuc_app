# Calendar Booking Workflow

A simple LangGraph implementation for booking Google Calendar appointments with intelligent LLM-based routing.

## Overview

This workflow implements a three-step process for booking calendar appointments:

1. **Fetch Available Slots** - Retrieves available time slots on Tuesday from 10:00-14:00
2. **Confirm Booking** - Locks in the selected slot and prompts for confirmation
3. **Book Appointment** - Creates the calendar event and verifies the booking

## Intelligent Routing

The agent uses **LLM-based intent classification** to intelligently route user queries:

- **Calendar Intent**: Queries about booking appointments, scheduling, or getting a time slot
- **RAG Intent**: Queries about information, services, or general questions

This approach is more robust than keyword matching and can understand natural language variations and context.

## Architecture

### Files Structure

```
KKUCAssistant/backend/app/
├── tools/
│   └── calendar_tools.py          # Three calendar tools
├── workflows/
│   └── calendar_workflow.py       # LangGraph workflow
└── tests/
    ├── google_calender_test.py    # Original test file
    └── test_calendar_workflow.py  # Workflow test script
```

### Components

#### 1. CalendarTools (`tools/calendar_tools.py`)

Three simple tools for calendar operations:

- **`fetch_available_slots()`** - Fetches available 1-hour slots on Tuesday 10:00-14:00
- **`confirm_booking(selected_slot)`** - Locks in the booking request
- **`book_appointment(slot, name)`** - Books the appointment and verifies it

#### 2. CalendarWorkflow (`workflows/calendar_workflow.py`)

LangGraph workflow with three sequential steps:

```python
step1_fetch_slots → step2_confirm_booking → step3_book_appointment → END
```

**State Management:**
```python
class CalendarState(TypedDict):
    available_slots: List[Dict]
    selected_slot: Optional[Dict]
    confirmation: Optional[Dict]
    booking_result: Optional[Dict]
    error: Optional[str]
```

## Usage

### Testing the Workflow

Test the calendar workflow directly:
```bash
cd KKUCAssistant/backend
python3 -m app.tests.test_calendar_workflow
```

Test the LLM-based routing:
```bash
cd KKUCAssistant/backend
python3 -m app.tests.test_agent_routing
```

### Using in Code

```python
from app.workflows.calendar_workflow import CalendarWorkflow

# Initialize workflow
workflow = CalendarWorkflow()

# Run the workflow
result = workflow.run()

# Check result
if result["success"]:
    print(f"Booked: {result['booking']['message']}")
else:
    print(f"Error: {result['error']}")
```

## Configuration

The workflow uses environment variables from `.env`:

```env
GOOGLE_CALENDAR_ID=your_calendar_id
GOOGLE_CALENDAR_TYPE=service_account
GOOGLE_CALENDAR_PROJECT_ID=your_project_id
GOOGLE_CALENDAR_PRIVATE_KEY_ID=your_key_id
GOOGLE_CALENDAR_PRIVATE_KEY=your_private_key
GOOGLE_CALENDAR_CLIENT_EMAIL=your_service_account_email
GOOGLE_CALENDAR_CLIENT_ID=your_client_id
GOOGLE_CALENDAR_AUTH_URI=https://accounts.google.com/o/oauth2/auth
GOOGLE_CALENDAR_TOKEN_URI=https://oauth2.googleapis.com/token
GOOGLE_CALENDAR_AUTH_PROVIDER_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
GOOGLE_CALENDAR_CLIENT_CERT_URL=your_cert_url
GOOGLE_CALENDAR_UNIVERSE_DOMAIN=googleapis.com
```

## Workflow Details

### Step 1: Fetch Available Slots

- Calculates next Tuesday
- Queries calendar for events between 10:00-14:00
- Identifies available 1-hour slots
- Auto-selects first available slot

### Step 2: Confirm Booking

- Locks in the selected slot
- Prepares confirmation message
- Returns confirmation details

### Step 3: Book Appointment

- Creates calendar event with name "testmus"
- Sends API request to Google Calendar
- Verifies booking by fetching the created event
- Returns confirmation with event details

## Example Output

```
============================================================
🚀 Starting Calendar Booking Workflow
============================================================

🚀 Step 1: Fetching Available Slots
✅ Found 4 available slots
✅ Auto-selected first slot: 10:00

🔒 Step 2: Confirming Booking Request
✅ Confirmation ready: Please confirm booking for Tuesday, 2025-10-14 at 10:00-11:00

📅 Step 3: Booking Appointment
✅ API call successful: Event ID 52cpu43tju5on4dmese5oqb34s
✅ Verification successful: Booking confirmed

============================================================
✅ Calendar Workflow Complete
============================================================

📊 WORKFLOW RESULTS
✅ Workflow completed successfully!
📅 Available slots found: 4
🎯 Selected slot: Tuesday, 2025-10-14 at 10:00
✅ Booking Status: confirmed
   Name: testmus
   Date: 2025-10-14
   Time: 10:00
   Event ID: 52cpu43tju5on4dmese5oqb34s
   Verified: True
```

## Key Features

- **Intelligent Routing** - LLM-based intent classification (no keyword matching!)
- **Minimal Complexity** - Simple, linear workflow with clear steps
- **Error Handling** - Graceful error handling at each step
- **Verification** - Double-checks booking by fetching created event
- **Auto-Selection** - Automatically selects first available slot
- **Time Zone Aware** - Uses Europe/Copenhagen timezone
- **1-Hour Slots** - Only considers slots that are at least 1 hour long
- **Natural Language** - Understands various ways users express booking intent

## Dependencies

- `langgraph` - For workflow orchestration
- `google-auth` - For Google Calendar authentication
- `google-api-python-client` - For Google Calendar API
- `pytz` - For timezone handling

## How It Works

### 1. User Query
User sends a message like:
- "Jeg vil gerne booke en tid"
- "Book din første tid"
- "Hvornår kan jeg komme?"

### 2. LLM Router
The agent uses an LLM to classify the intent:
```python
classification_prompt = """Du er en intent classifier for en KKUC assistent.

Brugerens besked: "{user_query}"

Bestem om brugeren ønsker at:
A) Booke en tid/aftale (calendar booking)
B) Få information fra KKUC's hjemmeside (RAG search)

Svar KUN med enten "calendar" eller "rag" - intet andet.
"""
```

### 3. Route to Workflow
- If **calendar intent** → Calendar Booking Workflow
- If **rag intent** → RAG Search Workflow

### 4. Execute & Respond
The appropriate workflow executes and returns a formatted response to the user.

## Testing Results

All routing tests pass with 100% accuracy:
```
✅ "Jeg vil gerne booke en tid" → calendar
✅ "Book din første tid" → calendar
✅ "Hvornår kan jeg komme?" → calendar
✅ "Hvad er KKUC?" → rag
✅ "Hvordan virker behandlingen?" → rag
✅ "Fortæl mig om misbrugsbehandling" → rag
```

## Notes

- The workflow currently auto-selects the first available slot
- All bookings are created under the name "testmus"
- Only Tuesday slots from 10:00-14:00 are considered
- Minimum slot duration is 1 hour
- LLM routing provides robust intent detection without brittle keyword matching
