"""
Minimalist Calendar Booking Subgraph
Simple LangGraph workflow with checkpoint logging and opt-out at each step
"""
from typing import TypedDict, Optional, Dict, List, Literal
from langgraph.graph import StateGraph, END
from datetime import datetime, timedelta
from app.tools.calendar_tools import CalendarTools


class CalendarState(TypedDict):
    """State for calendar booking workflow"""
    available_slots: List[Dict]
    selected_slot: Optional[Dict]
    booking_result: Optional[Dict]
    action: Literal["proceed", "opt_out"]
    cancelled: bool


def log_checkpoint(name: str, next_step: str):
    """Log current checkpoint and next step"""
    print(f"\n📍 Checkpoint: {name}")
    print(f"   ✅ Completed: {name}")
    print(f"   → Next step: {next_step}")


class CalendarSubgraph:
    """Calendar booking subgraph with interrupts and opt-out"""
    
    def __init__(self):
        self.calendar_tools = CalendarTools()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build simple calendar workflow with interrupts"""
        workflow = StateGraph(CalendarState)
        
        workflow.add_node("fetch_slots", self.fetch_slots_node)
        workflow.add_node("select_slot", self.select_slot_node)
        workflow.add_node("confirm_booking", self.confirm_booking_node)
        workflow.add_node("book_appointment", self.book_appointment_node)
        
        workflow.set_entry_point("fetch_slots")
        workflow.add_edge("fetch_slots", "select_slot")
        workflow.add_edge("select_slot", "confirm_booking")
        workflow.add_edge("confirm_booking", "book_appointment")
        workflow.add_edge("book_appointment", END)
        
        # Add interrupts to pause for user input
        return workflow.compile(interrupt_before=["select_slot", "book_appointment"])
    
    def fetch_slots_node(self, state: CalendarState) -> Dict:
        """Fetch available slots - checkpoint 1"""
        log_checkpoint("fetch_slots", "select_slot")
        
        try:
            slots = self.calendar_tools.fetch_available_slots()
            
            for slot in slots:
                if "datetime" in slot and hasattr(slot["datetime"], "isoformat"):
                    slot["datetime"] = slot["datetime"].isoformat()
            
            print(f"   ℹ️  Found {len(slots)} available slots")
            
            return {"available_slots": slots, "cancelled": False}
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"available_slots": [], "cancelled": False}
    
    def select_slot_node(self, state: CalendarState) -> Dict:
        """Wait for user slot selection - checkpoint 2"""
        if state.get("cancelled"):
            return {"cancelled": True}
        
        log_checkpoint("select_slot", "confirm_booking")
        
        slots = state["available_slots"]
        if not slots:
            return {"message": "Ingen ledige tider", "cancelled": True}
        
        slots_display = [
            {"index": i + 1, "day": s["day"], "date": s["date"], "time": s["time"]}
            for i, s in enumerate(slots)
        ]
        
        print(f"   ⏳ Waiting for user to select slot...")
        
        # Return slot information for user selection
        # In LangGraph 0.2.x, interrupts are handled through the state and checkpointer
        return {
            "available_slots": slots,
            "cancelled": False,
            "slots_display": slots_display
        }
    
    def confirm_booking_node(self, state: CalendarState) -> Dict:
        """Wait for booking confirmation - checkpoint 3"""
        if state.get("cancelled"):
            return {"cancelled": True}
        
        log_checkpoint("confirm_booking", "book_appointment")
        
        slot = state.get("selected_slot")
        if not slot:
            return {"message": "Ingen tid valgt", "cancelled": True}
        
        print(f"   ⏳ Waiting for confirmation...")
        
        # Return confirmation prompt for user
        # In LangGraph 0.2.x, confirmation is handled through the state
        return {
            "selected_slot": slot,
            "cancelled": False,
            "message": f"Bekræft booking: {slot['day']}, {slot['date']} kl. {slot['time']}"
        }
    
    def book_appointment_node(self, state: CalendarState) -> Dict:
        """Book the appointment - checkpoint 4"""
        if state.get("cancelled"):
            return {"cancelled": True, "message": "Booking annulleret"}
        
        log_checkpoint("book_appointment", "completed")
        
        slot = state.get("selected_slot")
        if not slot:
            return {"message": "Ingen tid at booke", "cancelled": True}
        
        print(f"   ⏳ Booking appointment...")
        
        try:
            result = self.calendar_tools.book_appointment(slot)
            
            if result.get("verified"):
                message = f"""✅ Din tid er booket!

📅 **Detaljer:**
- Dato: {result['date']}
- Tid: {result['time']}
- Status: Bekræftet ✓

{result.get('link', '')}"""
                print(f"   ✅ Booking successful")
            else:
                message = f"❌ Booking fejlede: {result.get('message', 'Ukendt fejl')}"
                print(f"   ❌ Booking failed")
            
            return {
                "booking_result": result,
                "message": message,
                "cancelled": False
            }
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"message": f"❌ Fejl: {str(e)}", "cancelled": True}
    
    def run(self, initial_state: Dict = None) -> Dict:
        """Execute the calendar workflow"""
        print("\n" + "="*50)
        print("🚀 Starting Calendar Booking Workflow")
        print("="*50)
        
        state = initial_state or {
            "available_slots": [],
            "selected_slot": None,
            "booking_result": None,
            "action": "proceed",
            "cancelled": False
        }
        
        try:
            result = self.graph.invoke(state)
            
            print("\n" + "="*50)
            if result.get("cancelled"):
                print("❌ Booking workflow ended - cancelled")
            else:
                print("✅ Booking workflow completed")
            print("="*50 + "\n")
            
            return result
        except Exception as e:
            print(f"\n❌ Workflow error: {e}")
            import traceback
            traceback.print_exc()
            return {"message": f"Fejl: {str(e)}", "cancelled": True}
