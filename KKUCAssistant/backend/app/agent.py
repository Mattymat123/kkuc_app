"""
Main KKUC Assistant Agent - Refactored with LangGraph checkpointing
State persists across messages without restarting the booking flow
"""
import os
from typing import TypedDict, List, Annotated, Literal, Optional, Dict, Any
from operator import add

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from datetime import datetime, timedelta
import pytz

from .workflows.simplified_rag_workflow import SimplifiedRAGWorkflow
from .tools.calendar_tools import CalendarTools

load_dotenv()


def merge_dict(left: Optional[Dict], right: Optional[Dict]) -> Optional[Dict]:
    """Custom reducer for dict merging"""
    if right is None:
        return left
    if left is None:
        return right
    return {**left, **right}


class AgentState(TypedDict):
    """
    State for KKUC agent following LangGraph best practices.
    - messages: List of conversation messages (uses 'add' reducer to append)
    - booking_data: Temporary booking data (slots, selection, etc.)
    """
    messages: Annotated[List[BaseMessage], add]
    booking_data: Annotated[Optional[Dict[str, Any]], merge_dict]


class KKUCAgent:
    """Main KKUC Assistant Agent with proper state management"""
    
    def __init__(self):
        """Initialize the agent with workflows"""
        self.rag_workflow = SimplifiedRAGWorkflow()
        self.calendar_tools = CalendarTools()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the main agent graph with routing to calendar or RAG"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("route_query", self.route_query_node)
        workflow.add_node("rag_search", self.rag_search_node)
        workflow.add_node("calendar_handler", self.calendar_handler_node)
        
        # Set entry point
        workflow.set_entry_point("route_query")
        
        # Add conditional routing
        workflow.add_conditional_edges(
            "route_query",
            self.should_use_calendar,
            {
                "calendar": "calendar_handler",
                "rag": "rag_search"
            }
        )
        
        # Both end after their node
        workflow.add_edge("rag_search", END)
        workflow.add_edge("calendar_handler", END)
        
        return workflow
    
    def route_query_node(self, state: AgentState) -> Dict[str, Any]:
        """Initial routing node - must return state update"""
        # Return empty list to satisfy LangGraph's requirement that nodes update state
        return {"messages": []}
    
    def should_use_calendar(self, state: AgentState) -> Literal["calendar", "rag"]:
        """Determine routing based on user input and existing booking state"""
        # Check if we're in the middle of a booking
        booking_data = state.get("booking_data")
        if booking_data and booking_data.get("step") in ["select", "confirm"]:
            print(f"🗓️  Continuing booking flow (step: {booking_data.get('step')})")
            return "calendar"
        
        last_message = state["messages"][-1]
        
        if isinstance(last_message, HumanMessage):
            user_input = last_message.content
            if isinstance(user_input, list):
                user_input = " ".join([
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in user_input
                ])
            
            user_input_lower = user_input.lower().strip()
            
            # Check for booking keywords
            booking_keywords = ["book", "tid", "aftale", "møde", "booking", "tirsdag", "onsdag"]
            if any(keyword in user_input_lower for keyword in booking_keywords):
                print(f"🗓️  Detected booking intent - routing to calendar")
                return "calendar"
            
            # Use LLM for intent classification
            llm = ChatOpenAI(
                model="anthropic/claude-sonnet-4.5",
                temperature=0,
                openai_api_key=os.getenv("OPENROUTER_API_KEY"),
                openai_api_base="https://openrouter.ai/api/v1"
            )
            
            classification_prompt = f"""Du er en intent classifier for en KKUC assistent.

Brugerens besked: "{user_input}"

Bestem om brugeren ønsker at:
A) Booke en tid/aftale (calendar booking)
B) Få information fra KKUC's hjemmeside (RAG search)

Svar KUN med enten "calendar" eller "rag" - intet andet."""
            
            try:
                response = llm.invoke([HumanMessage(content=classification_prompt)])
                intent = response.content.strip().lower()
                
                if "calendar" in intent:
                    print(f"🗓️  LLM Router: calendar intent")
                    return "calendar"
                else:
                    print(f"🔍 LLM Router: rag intent")
                    return "rag"
            except Exception as e:
                print(f"⚠️  Error in LLM routing: {e}")
                return "rag"
        
        return "rag"
    
    def calendar_handler_node(self, state: AgentState) -> Dict[str, Any]:
        """Handle calendar booking with state persistence"""
        print("\n📅 Processing calendar booking...")
        
        last_message = state["messages"][-1]
        user_input = last_message.content
        if isinstance(user_input, list):
            user_input = " ".join([
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in user_input
            ])
        
        booking_data = state.get("booking_data", {})
        current_step = booking_data.get("step", "start")
        
        print(f"📊 Current step: {current_step}")
        
        try:
            # Step 1: Fetch slots
            if current_step == "start":
                print("🔄 Step 1: Fetching slots...")
                available_slots = self.calendar_tools.fetch_available_slots()
                
                # Convert datetime objects to ISO strings
                for slot in available_slots:
                    if "datetime" in slot and hasattr(slot["datetime"], "isoformat"):
                        slot["datetime"] = slot["datetime"].isoformat()
                
                if available_slots:
                    slots_text = "\n".join([
                        f"{i+1}. {slot['day']}, {slot['date']} kl. {slot['time']}-{(datetime.fromisoformat(slot['datetime']) + timedelta(hours=1)).strftime('%H:%M')}"
                        for i, slot in enumerate(available_slots)
                    ])
                    
                    message = f"📅 Ledige tider på tirsdag og onsdag:\n\n{slots_text}\n\nVælg venligst et nummer (1-{len(available_slots)}):"
                    
                    return {
                        "messages": [AIMessage(content=message)],
                        "booking_data": {
                            "step": "select",
                            "available_slots": available_slots
                        }
                    }
                else:
                    return {
                        "messages": [AIMessage(content="❌ Beklager, der er ingen ledige tider på tirsdag og onsdag mellem 10:00-14:00.")],
                        "booking_data": None
                    }
            
            # Step 2: Process slot selection
            elif current_step == "select":
                print("🔢 Step 2: Processing slot selection...")
                available_slots = booking_data.get("available_slots", [])
                
                try:
                    selection = int(user_input.strip())
                    if 1 <= selection <= len(available_slots):
                        selected_slot = available_slots[selection - 1]
                        
                        message = f"📅 Du har valgt:\n{selected_slot['day']}, {selected_slot['date']} kl. {selected_slot['time']}\n\nBekræft venligst din booking (ja/nej):"
                        
                        return {
                            "messages": [AIMessage(content=message)],
                            "booking_data": {
                                "step": "confirm",
                                "available_slots": available_slots,
                                "selected_slot": selected_slot
                            }
                        }
                    else:
                        return {
                            "messages": [AIMessage(content=f"❌ Ugyldigt valg. Vælg venligst et nummer mellem 1 og {len(available_slots)}:")],
                            "booking_data": booking_data  # Keep current state
                        }
                except (ValueError, TypeError):
                    return {
                        "messages": [AIMessage(content=f"❌ Ugyldigt input. Vælg venligst et nummer mellem 1 og {len(available_slots)}:")],
                        "booking_data": booking_data  # Keep current state
                    }
            
            # Step 3: Process confirmation and book
            elif current_step == "confirm":
                print("✅ Step 3: Processing confirmation...")
                user_input_lower = user_input.lower().strip()
                
                if user_input_lower in ["ja", "yes", "y", "ok", "bekræft"]:
                    selected_slot = booking_data.get("selected_slot")
                    
                    if selected_slot:
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
                            "messages": [AIMessage(content=message)],
                            "booking_data": None  # Clear booking data
                        }
                    else:
                        return {
                            "messages": [AIMessage(content="❌ Ingen tid valgt")],
                            "booking_data": None
                        }
                else:
                    return {
                        "messages": [AIMessage(content="❌ Booking annulleret. Skriv 'book en tid' for at prøve igen.")],
                        "booking_data": None
                    }
            
            else:
                return {
                    "messages": [AIMessage(content="❌ Ukendt booking step. Skriv 'book en tid' for at starte forfra.")],
                    "booking_data": None
                }
                
        except Exception as e:
            print(f"⚠️  Error: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "messages": [AIMessage(content="Beklager, der opstod en fejl. Prøv igen. 💙")],
                "booking_data": None
            }
    
    def rag_search_node(self, state: AgentState) -> Dict[str, Any]:
        """Process RAG search"""
        last_message = state["messages"][-1]
        
        if isinstance(last_message, HumanMessage):
            user_query = last_message.content
            if isinstance(user_query, list):
                user_query = " ".join([
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in user_query
                ])
            
            conversation_history = state["messages"][:-1] if len(state["messages"]) > 1 else []
            
            try:
                result = self.rag_workflow.run(user_query, conversation_history)
                response = result['answer']
                
                return {
                    "messages": [AIMessage(content=response)]
                }
            except Exception as e:
                print(f"⚠️  RAG Error: {e}")
                return {
                    "messages": [AIMessage(content="Beklager, der opstod en fejl. Prøv igen. 💙")]
                }
        
        # Fallback - should not reach here but return empty messages list to satisfy LangGraph
        return {"messages": []}


# Create agent executor with checkpointing
def create_agent():
    """Create and return the agent executor with memory checkpointing"""
    agent = KKUCAgent()
    checkpointer = MemorySaver()
    return agent.graph.compile(checkpointer=checkpointer)


# Global agent instance
agent_executor = create_agent()
