"""
Calendar Booking Workflow using LangGraph with Interrupts
Interactive workflow with human-in-the-loop confirmation at each step
"""
from typing import TypedDict, Optional, List, Dict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.constants import interrupt
from ..tools.calendar_tools import CalendarTools
from datetime import datetime, timedelta
import pytz


class CalendarWorkflowState(TypedDict):
    """State for calendar booking workflow"""
    available_slots: List[Dict]
    selected_slot: Optional[Dict]
    booking_result: Optional[Dict]
    user_input: str
    message: str


class CalendarWorkflow:
    """Interactive calendar booking workflow with human-in-the-loop using interrupts"""
    
    def __init__(self):
        """Initialize calendar workflow"""
        self.calendar_tools = CalendarTools()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build interactive calendar workflow graph with interrupts"""
        workflow = StateGraph(CalendarWorkflowState)
        
        # Add nodes for each step
        workflow.add_node("fetch_slots", self.fetch_slots_node)
        workflow.add_node("select_slot", self.select_slot_node)
        workflow.add_node("confirm_booking", self.confirm_booking_node)
        workflow.add_node("book_appointment", self.book_appointment_node)
        
        # Set entry point
        workflow.set_entry_point("fetch_slots")
        
        # Add edges
        workflow.add_edge("fetch_slots", "select_slot")
        workflow.add_edge("select_slot", "confirm_booking")
        workflow.add_edge("confirm_booking", "book_appointment")
        workflow.add_edge("book_appointment", END)
        
        return workflow.compile()
    
    def fetch_slots_node(self, state: CalendarWorkflowState) -> Dict:
        """Fetch available slots"""
        print("\n📅 Fetching available slots...")
        
        try:
            available_slots = self.calendar_tools.fetch_available_slots()
            
            # Convert datetime objects to ISO strings for JSON serialization
            for slot in available_slots:
                if "datetime" in slot and hasattr(slot["datetime"], "isoformat"):
                    slot["datetime"] = slot["datetime"].isoformat()
            
            if available_slots:
                print(f"✅ Found {len(available_slots)} slots")
                return {
                    "available_slots": available_slots,
                    "message": "Slots fetched successfully"
                }
            else:
                print("❌ No slots available")
                return {
                    "available_slots": [],
                    "message": "Ingen ledige tider fundet"
                }
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                "available_slots": [],
                "message": f"Fejl ved hentning af tider: {str(e)}"
            }
    
    def select_slot_node(self, state: CalendarWorkflowState) -> Dict:
        """Present slots and wait for user selection using interrupt"""
        print("\n🔢 Waiting for slot selection...")
        
        available_slots = state["available_slots"]
        
        if not available_slots:
            return {"message": "Ingen ledige tider at vælge fra"}
        
        # Format slots for display
        slots_display = []
        for i, slot in enumerate(available_slots):
            slots_display.append({
                "index": i + 1,
                "day": slot["day"],
                "date": slot["date"],
                "time": slot["time"]
            })
        
        # Use interrupt to wait for user selection
        selection = interrupt({
            "type": "slot_selection",
            "slots": slots_display,
            "message": "Vælg venligst et nummer (1-{})".format(len(available_slots))
        })
        
        print(f"✅ User selected: {selection}")
        
        # Validate and get selected slot
        try:
            slot_index = int(selection) - 1
            if 0 <= slot_index < len(available_slots):
                selected_slot = available_slots[slot_index]
                return {
                    "selected_slot": selected_slot,
                    "message": f"Valgt: {selected_slot['day']}, {selected_slot['date']} kl. {selected_slot['time']}"
                }
            else:
                return {
                    "message": "Ugyldigt valg"
                }
        except (ValueError, TypeError):
            return {
                "message": "Ugyldigt input"
            }
    
    def confirm_booking_node(self, state: CalendarWorkflowState) -> Dict:
        """Ask for confirmation using interrupt"""
        print("\n✅ Waiting for booking confirmation...")
        
        selected_slot = state.get("selected_slot")
        
        if not selected_slot:
            return {"message": "Ingen tid valgt"}
        
        # Use interrupt to wait for confirmation
        confirmed = interrupt({
            "type": "booking_confirmation",
            "slot": {
                "day": selected_slot["day"],
                "date": selected_slot["date"],
                "time": selected_slot["time"]
            },
            "message": f"Bekræft booking: {selected_slot['day']}, {selected_slot['date']} kl. {selected_slot['time']}"
        })
        
        print(f"{'✅' if confirmed else '❌'} User {'confirmed' if confirmed else 'cancelled'}")
        
        if not confirmed:
            return {
                "message": "Booking annulleret"
            }
        
        return {
            "message": "Booking bekræftet, booker nu..."
        }
    
    def book_appointment_node(self, state: CalendarWorkflowState) -> Dict:
        """Book the appointment"""
        print("\n📅 Booking appointment...")
        
        selected_slot = state.get("selected_slot")
        
        if not selected_slot:
            return {"message": "Ingen tid at booke"}
        
        try:
            booking_result = self.calendar_tools.book_appointment(selected_slot)
            
            if booking_result.get("verified"):
                message = f"""✅ Din tid er booket!

📅 **Detaljer:**
- Dato: {booking_result['date']}
- Tid: {booking_result['time']}
- Status: Bekræftet ✓

Du kan se din booking her: {booking_result.get('link', 'N/A')}"""
                print("✅ Booking successful")
            else:
                message = f"❌ Booking fejlede: {booking_result.get('message', 'Unknown error')}"
                print(f"❌ Booking failed")
            
            return {
                "booking_result": booking_result,
                "message": message
            }
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                "message": f"❌ Fejl ved booking: {str(e)}"
            }
    
    def run(self, user_input: str, conversation_history: List) -> Dict:
        """
        Run the calendar workflow
        This is called by the agent and handles the entire booking flow
        """
        print("\n🚀 Starting calendar booking workflow...")
        
        try:
            # Initialize state
            initial_state = CalendarWorkflowState(
                available_slots=[],
                selected_slot=None,
                booking_result=None,
                user_input=user_input,
                message=""
            )
            
            # Run the workflow - it will pause at interrupts
            result = self.graph.invoke(initial_state)
            
            return {
                "message": result.get("message", "Booking completed"),
                "booking_result": result.get("booking_result")
            }
            
        except Exception as e:
            print(f"❌ Error in workflow: {e}")
            import traceback
            traceback.print_exc()
            return {
                "message": f"❌ Fejl: {str(e)}"
            }
