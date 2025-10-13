# Agent Context Flow Fix - October 13, 2025

## Problem Description

The agent was not properly maintaining booking context when users provided feedback or refinement requests during the booking flow. 

### Example Issue:
1. User: "Jeg vil gerne booke en tid" (I want to book a time)
2. Agent: Shows available slots (Tuesday 14th at 13:00, Wednesday 15th at 10:00, etc.)
3. User: "book tirsdag den 14" (book Tuesday the 14th)
4. Agent: **INCORRECTLY** restarted from step 1, showing all slots again instead of continuing the flow

## Root Cause

The routing logic in `should_use_calendar()` was not properly prioritizing ongoing booking sessions. When a user provided text like "book tirsdag den 14", the system would:

1. Detect calendar-related keywords
2. Route to calendar workflow
3. But NOT check if there was an existing booking session with available slots
4. Result: Start a NEW booking session instead of continuing the existing one

## Solution

### 1. Enhanced Routing Priority (agent.py)

Updated `should_use_calendar()` with a three-tier priority system:

**PRIORITY 1**: Check for ongoing booking session with available slots
```python
if booking_state:
    if booking_state.get("available_slots") and booking_state.get("step") in ["select", "confirm"]:
        print(f"🗓️  Continuing existing booking session (step: {booking_state.get('step')}, slots: {len(booking_state.get('available_slots', []))})")
        return "calendar"
```

**PRIORITY 2**: Check for numeric or confirmation input
```python
if user_input.strip().isdigit() and 1 <= int(user_input.strip()) <= 5:
    return "calendar"
if user_input_lower in ["ja", "nej", "yes", "no", "y", "n", "ok", "bekræft"]:
    return "calendar"
```

**PRIORITY 3**: Check for date/time refinement keywords when booking session exists
```python
if booking_state and booking_state.get("available_slots"):
    refinement_keywords = ["tirsdag", "onsdag", "den", "kl", "klokken", "tid", "time"]
    if any(keyword in user_input_lower for keyword in refinement_keywords):
        return "calendar"
```

### 2. Intelligent Text Matching (agent.py)

Enhanced `calendar_booking_node()` to handle text-based slot selection:

```python
except ValueError:
    # User didn't provide a number - try to match their text to a slot
    print(f"🔍 User provided text instead of number, attempting to match: '{user_input}'")
    
    # Use LLM to match user's text to available slots
    available_slots = booking_state.get("available_slots", [])
    slots_text = "\n".join([
        f"{i+1}. {slot['day']}, {slot['date']} kl. {slot['time']}"
        for i, slot in enumerate(available_slots)
    ])
    
    match_llm = ChatOpenAI(...)
    match_prompt = f"""Du skal matche brugerens besked til en af de ledige tider.

Ledige tider:
{slots_text}

Brugerens besked: "{user_input}"

Hvilket nummer (1-{len(available_slots)}) matcher brugerens ønske bedst?
Svar KUN med nummeret, intet andet."""
    
    match_response = match_llm.invoke([HumanMessage(content=match_prompt)])
    matched_number = int(match_response.content.strip())
```

## Benefits

1. **Maintains Context**: Agent now properly continues booking flow even when users provide additional context
2. **Flexible Input**: Users can select slots by:
   - Number (1, 2, 3, etc.)
   - Text description ("tirsdag den 14", "onsdag kl 10", etc.)
   - Natural language ("book Tuesday the 14th")
3. **No Restarts**: Eliminates frustrating flow restarts that confused users
4. **Better UX**: More natural conversation flow that feels intelligent and responsive

## Testing

Created comprehensive test suite in `test_agent_context_flow.py`:

### Test 1: Normal Flow with Number
- User requests booking
- Agent shows slots
- User selects with number "1"
- ✅ Agent continues to confirmation step

### Test 2: Flow with Text Refinement
- User requests booking
- Agent shows slots
- User provides text "book tirsdag den 14"
- ✅ Agent matches text to slot and continues to confirmation

Both tests pass successfully!

## Files Modified

1. **KKUCAssistant/backend/app/agent.py**
   - Enhanced `should_use_calendar()` routing logic
   - Added intelligent text matching in `calendar_booking_node()`

2. **KKUCAssistant/backend/app/tests/test_agent_context_flow.py** (NEW)
   - Comprehensive test suite for context flow

## Impact

This fix ensures the agentic flow is properly managed throughout the booking process, preventing the frustrating behavior where the agent would restart from step 1 after receiving user feedback. The system now intelligently maintains context and continues the conversation flow naturally.
