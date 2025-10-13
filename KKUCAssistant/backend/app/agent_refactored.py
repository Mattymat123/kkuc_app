"""
Main KKUC Assistant Agent - Refactored with proper LangGraph state management
Following best practices from: https://medium.com/@gitmaxd/understanding-state-in-langgraph-a-comprehensive-guide-191462220997
"""
import os
from typing import TypedDict, List, Annotated, Literal, Optional, Dict, Any
from operator import add

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from datetime import datetime
import pytz

from .workflows.simplified_rag_workflow import SimplifiedRAGWorkflow
from .workflows.calendar_workflow import CalendarWorkflow

load_dotenv()


def merge_booking_state(left: Optional[Dict], right: Optional[Dict]) -> Optional[Dict]:
    """
    Custom reducer for booking_state that properly merges state updates.
    This follows LangGraph best practices for state management.
    """
    if right is None:
        return left
    if left is None:
        return right
    
    # Merge the dictionaries, with right taking precedence
    merged = {**left, **right}
    return merged


class AgentState(TypedDict):
    """
    State for KKUC agent following LangGraph best practices.
    - messages: List of conversation messages (uses 'add' reducer to append)
    - booking_state: Booking workflow state (uses custom merger)
    """
    messages: Annotated[List[BaseMessage], add]
    booking_state: Annotated[Optional[Dict[str, Any]], merge_booking_state]


class KKUCAgent:
    """Main KKUC Assistant Agent with proper state management"""
    
    def __init__(self):
        """Initialize the agent with workflows"""
        self.rag_workflow = SimplifiedRAGWorkflow()
        self.calendar_workflow = CalendarWorkflow()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the main agent graph with routing to calendar or RAG"""
        workflow = StateGraph(AgentState)
        
        # Add nodes - each node returns partial state updates
        workflow.add_node("route_query", self.route_query_node)
        workflow.add_node("rag_search", self.rag_search_node)
        workflow.add_node("calendar_booking", self.calendar_booking_node)
        
        # Set entry point
        workflow.set_entry_point("route_query")
        
        # Add conditional routing
        workflow.add_conditional_edges(
            "route_query",
            self.should_use_calendar,
            {
                "calendar": "calendar_booking",
                "rag": "rag_search"
            }
        )
        
        # Both end after their node
        workflow.add_edge("rag_search", END)
        workflow.add_edge("calendar_booking", END)
        
        return workflow.compile()
    
    def route_query_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Initial routing node - returns empty dict (no state changes).
        Following LangGraph pattern: nodes return partial state updates.
        """
        return {}
    
    def should_use_calendar(self, state: AgentState) -> Literal["calendar", "rag"]:
        """Determine routing based on state and user input"""
        booking_state = state.get("booking_state")
        
        # PRIORITY 1: Continue existing booking session
        if booking_state and booking_state.get("available_slots") and booking_state.get("step") in ["select", "confirm"]:
            print(f"🗓️  Continuing booking session (step: {booking_state.get('step')})")
            return "calendar"
        
        # PRIORITY 2: Check for numeric/confirmation input
        last_message = state["messages"][-1]
        if isinstance(last_message, HumanMessage):
            user_input = last_message.content
            if isinstance(user_input, list):
                user_input = " ".join([
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in user_input
                ])
            
            user_input_lower = user_input.lower().strip()
            
            if user_input.strip().isdigit() and 1 <= int(user_input.strip()) <= 5:
                print(f"🗓️  Detected numeric input - routing to calendar")
                return "calendar"
            
            if user_input_lower in ["ja", "nej", "yes", "no", "y", "n", "ok", "bekræft"]:
                print(f"🗓️  Detected confirmation - routing to calendar")
                return "calendar"
            
            # PRIORITY 3: Check for refinement keywords with active booking
            if booking_state and booking_state.get("available_slots"):
                refinement_keywords = ["tirsdag", "onsdag", "den", "kl", "klokken", "tid", "time"]
                if any(keyword in user_input_lower for keyword in refinement_keywords):
                    print(f"🗓️  Detected booking refinement - routing to calendar")
                    return "calendar"
            
            # PRIORITY 4: Use LLM for intent classification
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
    
    def calendar_booking_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Process calendar booking - returns partial state update.
        Following LangGraph pattern: return dict with state changes only.
        """
        print("\n📅 Processing calendar booking...")
        
        last_message = state["messages"][-1]
        user_input = last_message.content
        if isinstance(user_input, list):
            user_input = " ".join([
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in user_input
            ])
        
        try:
            booking_state = state.get("booking_state")
            
            if booking_state:
                print(f"📊 Incoming state: step={booking_state.get('step')}, slots={len(booking_state.get('available_slots', []))}")
            else:
                print("📊 No incoming booking_state")
            
            context = ""
            new_booking_state = None
            
            # Step 1: Fetch available slots
            if not booking_state or booking_state.get("step") not in ["select", "confirm"]:
                print("🔄 Fetching available slots...")
                result = self.calendar_workflow.start()
                
                # Convert datetime objects to strings
                if result.get("available_slots"):
                    for slot in result["available_slots"]:
                        if "datetime" in slot and hasattr(slot["datetime"], "isoformat"):
                            slot["datetime"] = slot["datetime"].isoformat()
                
                new_booking_state = result
                
                if result.get("available_slots"):
                    slots_list = "\n".join([
                        f"{i+1}. {slot['day']}, {slot['date']} kl. {slot['time']}"
                        for i, slot in enumerate(result["available_slots"])
                    ])
                    context = f"Ledige tider:\n{slots_list}"
                else:
                    context = "Ingen ledige tider fundet"
            
            # Step 2: Process slot selection
            elif booking_state.get("step") == "select":
                print(f"🔢 Processing slot selection...")
                
                try:
                    selection = int(user_input.strip())
                    result = self.calendar_workflow.process_selection(selection, booking_state)
                    new_booking_state = result
                    
                    if result.get("selected_slot"):
                        slot = result["selected_slot"]
                        context = f"Bruger valgte: {slot['day']}, {slot['date']} kl. {slot['time']}"
                    else:
                        context = "Ugyldigt valg"
                except ValueError:
                    # Try LLM matching
                    print(f"🔍 Attempting text matching...")
                    available_slots = booking_state.get("available_slots", [])
                    slots_text = "\n".join([
                        f"{i+1}. {slot['day']}, {slot['date']} kl. {slot['time']}"
                        for i, slot in enumerate(available_slots)
                    ])
                    
                    match_llm = ChatOpenAI(
                        model="anthropic/claude-sonnet-4.5",
                        temperature=0,
                        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
                        openai_api_base="https://openrouter.ai/api/v1"
                    )
                    
                    match_prompt = f"""Ledige tider:
{slots_text}

Brugerens besked: "{user_input}"

Hvilket nummer (1-{len(available_slots)}) matcher bedst?
Svar KUN med nummeret."""
                    
                    try:
                        match_response = match_llm.invoke([HumanMessage(content=match_prompt)])
                        matched_number = int(match_response.content.strip())
                        
                        if 1 <= matched_number <= len(available_slots):
                            print(f"✅ Matched to slot #{matched_number}")
                            result = self.calendar_workflow.process_selection(matched_number, booking_state)
                            new_booking_state = result
                            
                            if result.get("selected_slot"):
                                slot = result["selected_slot"]
                                context = f"Bruger valgte: {slot['day']}, {slot['date']} kl. {slot['time']}"
                        else:
                            context = "Kunne ikke matche valg"
                            new_booking_state = booking_state  # Keep existing state
                    except Exception as e:
                        print(f"⚠️  Match error: {e}")
                        context = "Ugyldigt input"
                        new_booking_state = booking_state  # Keep existing state
            
            # Step 3: Process confirmation
            elif booking_state.get("step") == "confirm":
                print(f"✅ Processing confirmation...")
                confirmed = user_input.lower().strip() in ["ja", "yes", "y", "ok", "bekræft"]
                result = self.calendar_workflow.process_confirmation(confirmed, booking_state)
                new_booking_state = result
                
                if confirmed and result.get("booking_result"):
                    booking = result["booking_result"]
                    context = f"Booking bekræftet: {booking['date']} kl. {booking['time']}"
                elif not confirmed:
                    context = "Bruger annullerede"
                else:
                    context = "Booking fejlede"
            
            # Generate LLM response
            llm = ChatOpenAI(
                model="anthropic/claude-sonnet-4.5",
                temperature=0,
                openai_api_key=os.getenv("OPENROUTER_API_KEY"),
                openai_api_base="https://openrouter.ai/api/v1"
            )
            
            step = new_booking_state.get("step", "fetch") if new_booking_state else "fetch"
            danish_tz = pytz.timezone('Europe/Copenhagen')
            now_danish = datetime.now(danish_tz)
            
            danish_days = {
                'Monday': 'Mandag', 'Tuesday': 'Tirsdag', 'Wednesday': 'Onsdag',
                'Thursday': 'Torsdag', 'Friday': 'Fredag', 'Saturday': 'Lørdag', 'Sunday': 'Søndag'
            }
            danish_months = {
                'January': 'januar', 'February': 'februar', 'March': 'marts', 'April': 'april',
                'May': 'maj', 'June': 'juni', 'July': 'juli', 'August': 'august',
                'September': 'september', 'October': 'oktober', 'November': 'november', 'December': 'december'
            }
            
            day_name = danish_days.get(now_danish.strftime("%A"), now_danish.strftime("%A"))
            month_name = danish_months.get(now_danish.strftime("%B"), now_danish.strftime("%B"))
            current_date = f"{day_name} den {now_danish.day}. {month_name} {now_danish.year}"
            
            if step == "select":
                prompt = f"""Du er booking assistent for KKUC.
I DAG ER: {current_date}
Kontekst: {context}
Brugerens besked: "{user_input}"

Vis ledige tider og bed om valg (nummer 1-4). Vær venlig. Brug 💙"""
            elif step == "confirm":
                prompt = f"""Du er booking assistent for KKUC.
I DAG ER: {current_date}
Kontekst: {context}
Brugerens besked: "{user_input}"

Vis valgt tid og bed om bekræftelse (ja/nej). Vær venlig. Brug 💙"""
            elif step == "complete":
                prompt = f"""Du er booking assistent for KKUC.
I DAG ER: {current_date}
Kontekst: {context}
Brugerens besked: "{user_input}"

Bekræft booking med detaljer. Vær venlig. Brug 💙"""
            else:
                prompt = f"""Du er booking assistent for KKUC.
Noget gik galt. Bed brugeren prøve igen. Vær venlig. Brug 💙"""
            
            response = llm.invoke([HumanMessage(content=prompt)])
            
            # Return partial state update (LangGraph will merge it)
            return {
                "messages": [AIMessage(content=response.content)],
                "booking_state": new_booking_state
            }
            
        except Exception as e:
            print(f"⚠️  Error: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "messages": [AIMessage(content="Beklager, der opstod en fejl. Prøv igen. 💙")],
                "booking_state": None
            }
    
    def rag_search_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Process RAG search - returns partial state update.
        Following LangGraph pattern: return dict with state changes only.
        """
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
                
                # Return partial state update
                return {
                    "messages": [AIMessage(content=response)]
                }
            except Exception as e:
                print(f"⚠️  RAG Error: {e}")
                return {
                    "messages": [AIMessage(content="Beklager, der opstod en fejl. Prøv igen. 💙")]
                }
        
        return {}


# Create agent executor
def create_agent():
    """Create and return the agent executor"""
    agent = KKUCAgent()
    return agent.graph


# Global agent instance
agent_executor = create_agent()
