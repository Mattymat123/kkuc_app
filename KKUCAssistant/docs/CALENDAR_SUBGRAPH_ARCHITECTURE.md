# Calendar Subgraph Architecture - Minimalist Design

## 🎯 Overview

The new calendar booking workflow uses a **minimalist LangGraph subgraph** with:
- ✅ **Automatic booking mode locking** - Once booking starts, RAG cannot interrupt
- ✅ **Clear checkpoint logging** - Each step logs current checkpoint + next step
- ✅ **Opt-out at every step** - User can cancel at any point
- ✅ **Simple interrupt pattern** - Ready for generative UI integration

## 🏗️ Architecture

### Main Agent Flow

```
route_node
    ↓
route_decision (checks booking_active flag FIRST)
    ├─ If booking_active=True → calendar_node (LOCKED)
    └─ If booking_active=False → check intent
        ├─ Booking keywords/LLM says calendar → calendar_node
        └─ Otherwise → rag_node
```

### Calendar Subgraph Flow

```
fetch_slots
    ↓
[CHECKPOINT 1] fetch_slots
    ✅ Completed: fetch_slots
    → Next step: select_slot
    ↓
select_slot
    ↓
[CHECKPOINT 2] select_slot
    ✅ Completed: select_slot
    → Next step: confirm_booking
    [INTERRUPT - Wait for user]
        ├─ User selects slot → proceed
        └─ User opts out → exit
    ↓
confirm_booking
    ↓
[CHECKPOINT 3] confirm_booking
    ✅ Completed: confirm_booking
    → Next step: book_appointment
    [INTERRUPT - Wait for confirmation]
        ├─ User confirms → proceed
        └─ User opts out → exit
    ↓
book_appointment
    ↓
[CHECKPOINT 4] book_appointment
    ✅ Completed: book_appointment
    ✅ Booking successful!
```

## 🔒 How Booking Lock Works

The `booking_active` flag **prevents RAG switching**:

```python
def route_decision(self, state: AgentState) -> Literal["calendar", "rag"]:
    # First check: Is booking active?
    if state.get("booking_active"):
        print(f"🔒 Booking active - routing to calendar (locked)")
        return "calendar"  # ← NO OTHER PATH POSSIBLE
    
    # Only check intent if booking_active is False
    # ... rest of routing logic
```

**Behavior:**
- User starts booking → routing locked to calendar
- User completes/cancels booking → `booking_active = False` → RAG accessible again

## 📍 Checkpoint Logging

Each checkpoint logs:

```python
def log_checkpoint(name: str, next_step: str):
    print(f"\n📍 Checkpoint: {name}")
    print(f"   ✅ Completed: {name}")
    print(f"   → Next step: {next_step}")
```

**Example Output:**
```
🚀 Starting Calendar Booking Workflow
==================================================

📍 Checkpoint: fetch_slots
   ✅ Completed: fetch_slots
   → Next step: select_slot
   ℹ️  Found 6 available slots

📍 Checkpoint: select_slot
   ✅ Completed: select_slot
   → Next step: confirm_booking
   ⏳ Waiting for user to select slot...
   
[USER SELECTS SLOT 2]

   ✓ User selected slot 2

📍 Checkpoint: confirm_booking
   ✅ Completed: confirm_booking
   → Next step: book_appointment
   ⏳ Waiting for confirmation...

[USER CONFIRMS]

   ✓ User confirmed booking

📍 Checkpoint: book_appointment
   ✅ Completed: book_appointment
   ✅ Booking successful

✅ Booking workflow completed
==================================================
```

## 🛑 Opt-Out Handling

At each step, users can opt out:

```python
action_data = interrupt({
    "type": "select_slot",
    "checkpoint": "select_slot",
    "next_checkpoint": "confirm_booking",
    "slots": slots_display,
})

if action_data.get("action") == "opt_out":
    print(f"   ❌ User opted out")
    return {"cancelled": True}  # ← Exits workflow
```

When user opts out:
1. `cancelled` flag is set to `True`
2. All remaining nodes check this flag and skip execution
3. Workflow exits gracefully
4. User returned to main agent (can use RAG again)

## 🔌 Frontend Integration

### Interrupt Format

The calendar sends interrupts in this format:

```json
{
  "type": "select_slot",
  "checkpoint": "select_slot",
  "next_checkpoint": "confirm_booking",
  "slots": [
    {"index": 1, "day": "Tirsdag", "date": "2025-10-21", "time": "10:00"},
    {"index": 2, "day": "Tirsdag", "date": "2025-10-21", "time": "11:00"}
  ],
  "message": "Vælg en tid (1-6) eller annuller"
}
```

### Resume Format

Your generative UI should send back:

**For slot selection:**
```json
{
  "action": "proceed",
  "selection": 2
}
```

**For confirmation:**
```json
{
  "action": "proceed",
  "confirmed": true
}
```

**For opt-out (any step):**
```json
{
  "action": "opt_out"
}
```

## 📋 State Shape

```python
class AgentState(TypedDict):
    messages: List[BaseMessage]              # Conversation messages
    booking_active: bool                     # Booking mode flag (prevents RAG)
    booking_context: Optional[Dict]          # Context for current booking
```

## ✅ Guarantees

✅ **No RAG during booking** - `booking_active` prevents switching
✅ **Clear progression** - Each checkpoint logs current + next step
✅ **User control** - Can opt-out at any checkpoint
✅ **Simple code** - ~200 lines for entire workflow
✅ **Generative UI ready** - Interrupt data includes all needed context

## 🧪 Testing

To test the workflow:

1. Start booking: "Jeg vil gerne booke en tid"
2. Check console for checkpoint logging
3. At interrupt, send: `{"action": "proceed", "selection": 1}`
4. At confirmation, send: `{"action": "proceed", "confirmed": true}`
5. Verify booking completes
6. Verify RAG works again: "Hvad er jeres åbningstider?"

## 🔧 Customization

To add more checkpoints:

1. Add new node to `CalendarSubgraph._build_graph()`
2. Call `log_checkpoint("name", "next_step")` at start
3. Use `interrupt()` to pause for user input
4. Check `state.get("cancelled")` to handle opt-outs

That's it! No complex routing needed.
