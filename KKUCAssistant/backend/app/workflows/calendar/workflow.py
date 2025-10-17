"""
Calendar Booking Workflow
Handles the complete multi-step booking flow with state management
Matches the RAG architecture pattern
"""
from typing import TypedDict, Optional, Dict, List, Annotated, Any
from operator import add
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from .tools.calendar_tools import CalendarTools


class CalendarState(TypedDict):
    """State for calendar booking workflow"""
    messages: Annotated[List[BaseMessage], add]
    booking_active: bool
    booking_context: Optional[Dict[str, Any]]
    # booking_context contains:
    # - step: str (current step in workflow)
    # - available_slots: List[Dict] (available time slots)
    # - selected_slot: Dict (user's selected time slot)
    # - booking_details: Dict (substance_type, kommune, age_group, notes)


class CalendarWorkflow:
    """Calendar booking workflow - matches RAG architecture"""
    
    def __init__(self):
        self.calendar_tools = CalendarTools()
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute calendar booking workflow
        Returns updated state with messages and booking status
        """
        booking_context = state.get("booking_context") or {}
        current_step = booking_context.get("step", "fetch_slots")
        
        print(f"\n📅 Calendar Handler: Step = {current_step}")
        
        # Check for cancellation
        if state.get("messages"):
            last_msg = state["messages"][-1]
            if isinstance(last_msg, HumanMessage):
                user_input = last_msg.content
                if isinstance(user_input, list):
                    user_input = " ".join([str(block.get("text", "")) if isinstance(block, dict) else str(block) for block in user_input])
                
                if "annuller" in user_input.lower() or "cancel" in user_input.lower():
                    print("   ❌ User cancelled booking")
                    return {
                        "messages": [AIMessage(content="Booking annulleret. Spørg hvis du vil prøve igen! 💙")],
                        "booking_active": False,
                        "booking_context": None
                    }
        
        try:
            # Step 1: Fetch slots
            if current_step == "fetch_slots":
                return self._step1_fetch_slots(state)
            
            # Step 2: Process slot selection
            elif current_step == "select_slot":
                return self._step2_select_slot(state, booking_context)
            
            # Step 3: Collect booking details
            elif current_step == "collect_details":
                return self._step3_collect_details(state, booking_context)
            
            # Step 4: Confirm and book
            elif current_step == "confirm_booking":
                return self._step4_confirm_and_book(state, booking_context)
            
            else:
                # Unknown step, reset
                return {
                    "messages": [AIMessage(content="Fejl i booking flow. Prøv igen.")],
                    "booking_active": False,
                    "booking_context": None
                }
                
        except Exception as e:
            print(f"❌ Calendar error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "messages": [AIMessage(content="Beklager, der opstod en fejl. Prøv igen. 💙")],
                "booking_active": False,
                "booking_context": None
            }
    
    def _step1_fetch_slots(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Step 1: Fetch available slots"""
        if not state.get("booking_active"):
            print("   🔓 → 🔒 Locked into calendar workflow")
        
        slots = self.calendar_tools.fetch_available_slots()
        
        for slot in slots:
            if "datetime" in slot and hasattr(slot["datetime"], "isoformat"):
                slot["datetime"] = slot["datetime"].isoformat()
        
        if not slots:
            return {
                "messages": [AIMessage(content="Ingen ledige tider tilgængelige. 😔")],
                "booking_active": False,
                "booking_context": None
            }
        
        # Format slots as JSON for the TimeSlotPicker component
        import json
        slots_json = json.dumps({"slots": slots})
        
        message = f"""✅ Vælg din ønskede tid:

```calendar-slots
{slots_json}
```"""
        
        print(f"   ℹ️  Found {len(slots)} available slots")
        print("   ⏳ Waiting for user slot selection...")
        
        return {
            "messages": [AIMessage(content=message)],
            "booking_active": True,
            "booking_context": {
                "available_slots": slots,
                "step": "select_slot"
            }
        }
    
    def _step2_select_slot(self, state: Dict[str, Any], booking_context: Dict) -> Dict[str, Any]:
        """Step 2: Process slot selection and show booking details form"""
        slots = booking_context.get("available_slots", [])
        last_msg = state["messages"][-1]
        user_input = last_msg.content
        
        if isinstance(user_input, list):
            user_input = " ".join([str(block.get("text", "")) if isinstance(block, dict) else str(block) for block in user_input])
        
        # Try to extract slot number
        try:
            slot_num = int(user_input.strip()) - 1
            if 0 <= slot_num < len(slots):
                selected_slot = slots[slot_num]
                
                # Format slot data for BookingDetailsForm
                import json
                form_data = json.dumps({"selectedSlot": selected_slot})
                
                message = f"""📋 Udfyld booking detaljer:

```booking-details
{form_data}
```"""
                
                print(f"   ✅ Slot selected: {selected_slot['day']} {selected_slot['time']}")
                print("   ⏳ Waiting for booking details form submission...")
                
                return {
                    "messages": [AIMessage(content=message)],
                    "booking_active": True,
                    "booking_context": {
                        "available_slots": slots,
                        "selected_slot": selected_slot,
                        "step": "collect_details"
                    }
                }
            else:
                return {
                    "messages": [AIMessage(content=f"Ugyldigt nummer. Vælg mellem 1 og {len(slots)}.")],
                    "booking_active": True,
                    "booking_context": booking_context
                }
        except ValueError:
            return {
                "messages": [AIMessage(content="Skriv et tal for at vælge en tid.")],
                "booking_active": True,
                "booking_context": booking_context
            }
    
    def _step3_collect_details(self, state: Dict[str, Any], booking_context: Dict) -> Dict[str, Any]:
        """Step 3: Collect booking details from form"""
        last_msg = state["messages"][-1]
        user_input = last_msg.content
        
        if isinstance(user_input, list):
            user_input = " ".join([str(block.get("text", "")) if isinstance(block, dict) else str(block) for block in user_input])
        
        # Try to parse JSON form data
        try:
            import json
            booking_details = json.loads(user_input.strip())
            
            print(f"   📝 Raw booking details received: {booking_details}")
            
            # Validate required fields (notes is optional)
            required_fields = ['name', 'phone', 'substanceType', 'kommune', 'ageGroup']
            if not all(field in booking_details for field in required_fields):
                return {
                    "messages": [AIMessage(content="Fejl: Udfyld venligst alle felter i formularen.")],
                    "booking_active": True,
                    "booking_context": booking_context
                }
            
            # Validate phone number (Danish format)
            import re
            phone = booking_details.get('phone', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            danish_phone_regex = r'^(\+45)?[2-9]\d{7}$'
            if not re.match(danish_phone_regex, phone):
                return {
                    "messages": [AIMessage(content="Fejl: Ugyldigt telefonnummer. Indtast et gyldigt dansk telefonnummer (8 cifre).")],
                    "booking_active": True,
                    "booking_context": booking_context
                }
            
            selected_slot = booking_context.get("selected_slot")
            
            # Format booking confirmation data for BookingConfirmation component
            import json
            confirmation_data = json.dumps({
                "bookingData": {
                    "name": booking_details['name'],
                    "phone": booking_details['phone'],
                    "selectedSlot": selected_slot,
                    "substanceType": booking_details['substanceType'],
                    "kommune": booking_details['kommune'],
                    "ageGroup": booking_details['ageGroup'],
                    "notes": booking_details['notes']
                }
            })
            
            message = f"""📋 Gennemgå og bekræft din booking:

```booking-confirmation
{confirmation_data}
```"""
            
            print(f"   ✅ Booking details collected:")
            print(f"      Name: {booking_details['name']}")
            print(f"      Phone: {booking_details['phone']}")
            print(f"      Type: {booking_details['substanceType']}")
            print(f"      Kommune: {booking_details['kommune']}")
            print(f"      Age: {booking_details['ageGroup']}")
            print("   ⏳ Waiting for final confirmation with terms acceptance...")
            
            return {
                "messages": [AIMessage(content=message)],
                "booking_active": True,
                "booking_context": {
                    **booking_context,
                    "booking_details": booking_details,
                    "step": "confirm_booking"
                }
            }
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"   ❌ Failed to parse booking details: {e}")
            return {
                "messages": [AIMessage(content="Fejl ved behandling af formularen. Prøv igen.")],
                "booking_active": True,
                "booking_context": booking_context
            }
    
    def _step4_confirm_and_book(self, state: Dict[str, Any], booking_context: Dict) -> Dict[str, Any]:
        """Step 4: Confirm and book appointment"""
        last_msg = state["messages"][-1]
        user_input = last_msg.content
        
        if isinstance(user_input, list):
            user_input = " ".join([str(block.get("text", "")) if isinstance(block, dict) else str(block) for block in user_input])
        
        user_input_stripped = user_input.strip()
        
        # Check if user confirmed (either "CONFIRMED" from UI or "ja"/"yes" text)
        if user_input_stripped == "CONFIRMED" or "ja" in user_input_stripped.lower() or "yes" in user_input_stripped.lower():
            selected_slot = booking_context.get("selected_slot")
            booking_details = booking_context.get("booking_details")
            
            print(f"   ⏳ Booking appointment with collected details...")
            result = self.calendar_tools.book_appointment(selected_slot, booking_details=booking_details)
            
            if result.get("verified"):
                message = f"""✅ Din tid er booket!

📅 **Detaljer:**
- Dato: {result['date']}
- Tid: {result['time']}
- Status: Bekræftet ✓

{result.get('link', '')}"""
                print(f"   ✅ Booking successful")
                print("   🔒 → 🔓 Released from calendar workflow")
            else:
                message = f"❌ Booking fejlede: {result.get('message', 'Ukendt fejl')}"
                print(f"   ❌ Booking failed")
            
            return {
                "messages": [AIMessage(content=message)],
                "booking_active": False,
                "booking_context": None
            }
        else:
            return {
                "messages": [AIMessage(content="Skriv 'ja' for at bekræfte eller 'annuller' for at fortryde.")],
                "booking_active": True,
                "booking_context": booking_context
            }


# Create instance for backward compatibility with existing code
CalendarSubgraph = CalendarWorkflow
