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
            
            # Step 3: Confirm and book
            elif current_step == "confirm_booking":
                return self._step3_confirm_and_book(state, booking_context)
            
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
        """Step 2: Process slot selection"""
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
                
                message = f"""Du har valgt:
📅 {selected_slot['day']}, {selected_slot['date']} kl. {selected_slot['time']}

Bekræft ved at skrive 'ja' eller 'annuller' for at fortryde."""
                
                print(f"   ✅ Slot selected: {selected_slot['day']} {selected_slot['time']}")
                print("   ⏳ Waiting for confirmation...")
                
                return {
                    "messages": [AIMessage(content=message)],
                    "booking_active": True,
                    "booking_context": {
                        "available_slots": slots,
                        "selected_slot": selected_slot,
                        "step": "confirm_booking"
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
    
    def _step3_confirm_and_book(self, state: Dict[str, Any], booking_context: Dict) -> Dict[str, Any]:
        """Step 3: Confirm and book appointment"""
        last_msg = state["messages"][-1]
        user_input = last_msg.content
        
        if isinstance(user_input, list):
            user_input = " ".join([str(block.get("text", "")) if isinstance(block, dict) else str(block) for block in user_input])
        
        user_input_lower = user_input.lower().strip()
        
        if "ja" in user_input_lower or "yes" in user_input_lower:
            selected_slot = booking_context.get("selected_slot")
            
            print(f"   ⏳ Booking appointment...")
            result = self.calendar_tools.book_appointment(selected_slot)
            
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
