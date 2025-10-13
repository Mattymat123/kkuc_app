"""
Main KKUC Assistant Agent
Orchestrates different workflows (RAG, etc.) using LangGraph
Compatible with LangServe deployment
"""
import os
from typing import TypedDict, List, Annotated, Literal, Optional
from operator import add

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from datetime import timedelta, datetime
import pytz

from .workflows.simplified_rag_workflow import SimplifiedRAGWorkflow
from .workflows.calendar_workflow import CalendarWorkflow

load_dotenv()


class AgentState(TypedDict):
    """State for KKUC agent - compatible with LangServe"""
    messages: Annotated[List[BaseMessage], add]
    booking_state: Optional[dict]  # Track ongoing booking workflow state


class KKUCAgent:
    """Main KKUC Assistant Agent"""
    
    def __init__(self):
        """Initialize the agent with workflows"""
        # Initialize workflows
        self.rag_workflow = SimplifiedRAGWorkflow()
        self.calendar_workflow = CalendarWorkflow()
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the main agent graph with routing to calendar or RAG"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
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
        
        # Enable streaming for the graph
        return workflow.compile()
    
    def route_query_node(self, state: AgentState) -> AgentState:
        """Initial routing node - just passes through"""
        return state
    
    def should_use_calendar(self, state: AgentState) -> Literal["calendar", "rag"]:
        """Use LLM to intelligently determine if query is about booking an appointment"""
        # PRIORITY 1: Check if there's an ongoing booking session with available slots
        # This ensures we continue the booking flow even if user provides additional context
        booking_state = state.get("booking_state")
        if booking_state:
            # If we have available slots and are in select/confirm step, ALWAYS continue the booking
            if booking_state.get("available_slots") and booking_state.get("step") in ["select", "confirm"]:
                print(f"🗓️  Continuing existing booking session (step: {booking_state.get('step')}, slots: {len(booking_state.get('available_slots', []))})")
                return "calendar"
        
        # PRIORITY 2: Check if user is responding with a number or confirmation
        last_message = state["messages"][-1]
        if isinstance(last_message, HumanMessage):
            user_input = last_message.content
            if isinstance(user_input, list):
                user_input = " ".join([
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in user_input
                ])
            
            user_input_lower = user_input.lower().strip()
            
            # If user types a number 1-5, they're likely selecting a slot
            if user_input.strip().isdigit() and 1 <= int(user_input.strip()) <= 5:
                print(f"🗓️  Detected numeric input ({user_input.strip()}) - routing to calendar")
                return "calendar"
            
            # If user types ja/nej, they're likely confirming
            if user_input_lower in ["ja", "nej", "yes", "no", "y", "n", "ok", "bekræft"]:
                print(f"🗓️  Detected confirmation input ({user_input.strip()}) - routing to calendar")
                return "calendar"
            
            # PRIORITY 3: Check if user is providing feedback/refinement on existing booking
            # Look for date/time references when we have an active booking session
            if booking_state and booking_state.get("available_slots"):
                # Keywords that suggest user is refining their selection
                refinement_keywords = ["tirsdag", "onsdag", "den", "kl", "klokken", "tid", "time"]
                if any(keyword in user_input_lower for keyword in refinement_keywords):
                    print(f"🗓️  Detected refinement of existing booking - routing to calendar")
                    return "calendar"
        
        if isinstance(last_message, HumanMessage):
            user_query = last_message.content
            if isinstance(user_query, list):
                user_query = " ".join([
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in user_query
                ])
            
            # Use LLM to classify intent
            llm = ChatOpenAI(
                model="anthropic/claude-sonnet-4.5",
                temperature=0,
                openai_api_key=os.getenv("OPENROUTER_API_KEY"),
                openai_api_base="https://openrouter.ai/api/v1"
            )
            
            classification_prompt = f"""Du er en intent classifier for en KKUC assistent.

Brugerens besked: "{user_query}"

Bestem om brugeren ønsker at:
A) Booke en tid/aftale (calendar booking)
B) Få information fra KKUC's hjemmeside (RAG search)

Svar KUN med enten "calendar" eller "rag" - intet andet.

Eksempler på calendar intent:
- "Jeg vil gerne booke en tid"
- "Book din første tid"
- "Kan jeg få en aftale?"
- "Hvornår kan jeg komme?"

Eksempler på rag intent:
- "Hvad er KKUC?"
- "Hvordan virker behandlingen?"
- "Hvad er jeres åbningstider?"
- "Fortæl mig om misbrugsbehandling"

Svar:"""
            
            try:
                response = llm.invoke([HumanMessage(content=classification_prompt)])
                intent = response.content.strip().lower()
                
                if "calendar" in intent:
                    print(f"🗓️  LLM Router: Detected calendar booking intent")
                    return "calendar"
                else:
                    print(f"🔍 LLM Router: Detected information search intent")
                    return "rag"
                    
            except Exception as e:
                print(f"⚠️  Error in LLM routing, defaulting to RAG: {e}")
                return "rag"
        
        return "rag"
    
    def calendar_booking_node(self, state: AgentState) -> AgentState:
        """Process calendar booking request using LLM with tools"""
        print("\n📅 Processing calendar booking request with LLM...")
        
        last_message = state["messages"][-1]
        user_input = last_message.content
        if isinstance(user_input, list):
            user_input = " ".join([
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in user_input
            ])
        
        try:
            booking_state = state.get("booking_state")
            
            # Debug: Print incoming booking_state
            if booking_state:
                print(f"📊 Incoming booking_state: step={booking_state.get('step')}, has_slots={bool(booking_state.get('available_slots'))}")
            else:
                print("📊 No incoming booking_state")
            
            # Prepare context for LLM
            context = ""
            
            # Step 1: Start booking - fetch available slots (only if no existing booking_state)
            if not booking_state or (booking_state.get("step") not in ["select", "confirm"]):
                print("🔄 Fetching new available slots...")
                result = self.calendar_workflow.start()
                
                # Convert datetime objects to strings before storing in state
                if result.get("available_slots"):
                    for slot in result["available_slots"]:
                        if "datetime" in slot and hasattr(slot["datetime"], "isoformat"):
                            slot["datetime"] = slot["datetime"].isoformat()
                
                state["booking_state"] = result
                
                if result.get("available_slots"):
                    try:
                        # Format slots - simple format without end time calculation
                        slots_list = "\n".join([
                            f"{i+1}. {slot['day']}, {slot['date']} kl. {slot['time']}"
                            for i, slot in enumerate(result["available_slots"])
                        ])
                        context = f"Ledige tider:\n{slots_list}"
                        print(f"✅ Successfully formatted {len(result['available_slots'])} slots")
                    except Exception as format_error:
                        print(f"⚠️  Error formatting slots list: {format_error}")
                        import traceback
                        traceback.print_exc()
                        context = "Fejl ved formatering af ledige tider"
                else:
                    context = "Ingen ledige tider fundet"
            
            # Step 2: Process slot selection (use existing booking_state)
            elif booking_state.get("step") == "select":
                print(f"🔢 Processing slot selection with {len(booking_state.get('available_slots', []))} available slots")
                
                # Try to parse as a number first
                try:
                    selection = int(user_input.strip())
                    result = self.calendar_workflow.process_selection(selection, booking_state)
                    state["booking_state"] = result
                    
                    if result.get("selected_slot"):
                        slot = result["selected_slot"]
                        context = f"Bruger valgte: {slot['day']}, {slot['date']} kl. {slot['time']}"
                    else:
                        context = "Ugyldigt valg"
                except ValueError:
                    # User didn't provide a number - try to match their text to a slot
                    print(f"🔍 User provided text instead of number, attempting to match: '{user_input}'")
                    
                    # Use LLM to match user's text to available slots
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
                    
                    match_prompt = f"""Du skal matche brugerens besked til en af de ledige tider.

Ledige tider:
{slots_text}

Brugerens besked: "{user_input}"

Hvilket nummer (1-{len(available_slots)}) matcher brugerens ønske bedst?
Svar KUN med nummeret, intet andet."""
                    
                    try:
                        match_response = match_llm.invoke([HumanMessage(content=match_prompt)])
                        matched_number = int(match_response.content.strip())
                        
                        if 1 <= matched_number <= len(available_slots):
                            print(f"✅ LLM matched user input to slot #{matched_number}")
                            result = self.calendar_workflow.process_selection(matched_number, booking_state)
                            state["booking_state"] = result
                            
                            if result.get("selected_slot"):
                                slot = result["selected_slot"]
                                context = f"Bruger valgte: {slot['day']}, {slot['date']} kl. {slot['time']}"
                            else:
                                context = "Ugyldigt valg"
                        else:
                            context = "Kunne ikke matche brugerens valg til en ledig tid"
                    except Exception as match_error:
                        print(f"⚠️  Error matching user input: {match_error}")
                        context = "Bruger indtastede ikke et gyldigt nummer eller dato"
            
            # Step 3: Process confirmation (use existing booking_state)
            elif booking_state.get("step") == "confirm":
                print(f"✅ Processing confirmation for slot: {booking_state.get('selected_slot', {}).get('time')}")
                confirmed = user_input.lower().strip() in ["ja", "yes", "y", "ok", "bekræft"]
                result = self.calendar_workflow.process_confirmation(confirmed, booking_state)
                state["booking_state"] = result
                
                if confirmed and result.get("booking_result"):
                    booking = result["booking_result"]
                    context = f"Booking bekræftet: {booking['date']} kl. {booking['time']}, Event ID: {booking.get('event_id')}, Link: {booking.get('link')}"
                elif not confirmed:
                    context = "Bruger annullerede booking"
                else:
                    context = "Booking fejlede"
            
            # Use LLM to generate response based on context
            llm = ChatOpenAI(
                model="anthropic/claude-sonnet-4.5",
                temperature=0,
                openai_api_key=os.getenv("OPENROUTER_API_KEY"),
                openai_api_base="https://openrouter.ai/api/v1"
            )
            
            # Create prompt for LLM with current date context in Danish timezone
            # Get step from the UPDATED booking_state in state
            step = state.get("booking_state", {}).get("step", "fetch")
            danish_tz = pytz.timezone('Europe/Copenhagen')
            now_danish = datetime.now(danish_tz)
            
            # Manual Danish day/month names
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
                prompt = f"""Du er en hjælpsom booking assistent for KKUC.

I DAG ER: {current_date}

Kontekst: {context}

Brugerens besked: "{user_input}"

Vis de ledige tider i en pæn liste og bed brugeren vælge et nummer (1-4). Vær venlig og empatisk. Brug emojis 💙

VIGTIGT: Datoerne i konteksten er de faktiske ledige tider. Præsenter dem som de er."""
            
            elif step == "confirm":
                prompt = f"""Du er en hjælpsom booking assistent for KKUC.

I DAG ER: {current_date}

Kontekst: {context}

Brugerens besked: "{user_input}"

Vis den valgte tid og bed brugeren bekræfte med "ja" eller "nej". Vær venlig og empatisk. Brug emojis 💙"""
            
            elif step == "complete":
                prompt = f"""Du er en hjælpsom booking assistent for KKUC.

I DAG ER: {current_date}

Kontekst: {context}

Brugerens besked: "{user_input}"

Bekræft at tiden er booket med alle detaljer (dato, tid, link). Vær venlig og empatisk. Brug emojis 💙"""
            
            else:
                prompt = f"""Du er en hjælpsom booking assistent for KKUC.

I DAG ER: {current_date}

Kontekst: {context}

Brugerens besked: "{user_input}"

Noget gik galt. Bed brugeren prøve igen. Vær venlig og empatisk. Brug emojis 💙"""
            
            # Get LLM response (this will stream!)
            response = llm.invoke([HumanMessage(content=prompt)])
            
            state["messages"].append(AIMessage(content=response.content))
            
            # Debug: Print booking state
            print(f"✅ Calendar booking step completed with LLM")
            print(f"📊 Current booking state: step={state.get('booking_state', {}).get('step')}")
            if state.get("booking_state"):
                print(f"   Available slots: {len(state['booking_state'].get('available_slots', []))}")
                print(f"   Selected slot: {state['booking_state'].get('selected_slot')}")
            
        except Exception as e:
            print(f"⚠️  Error in calendar workflow: {e}")
            import traceback
            traceback.print_exc()
            state["messages"].append(AIMessage(
                content="Beklager, der opstod en fejl ved booking af tid. Prøv venligst igen. 💙"
            ))
            state["booking_state"] = None
        
        return state
    
    def rag_search_node(self, state: AgentState) -> AgentState:
        """Process user query through RAG workflow"""
        last_message = state["messages"][-1]
        
        if isinstance(last_message, HumanMessage):
            # Handle both string and list content
            user_query = last_message.content
            if isinstance(user_query, list):
                # Extract text from list of content blocks
                user_query = " ".join([
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in user_query
                ])
            
            # Pass conversation history to RAG workflow (excluding current query)
            conversation_history = state["messages"][:-1] if len(state["messages"]) > 1 else []
            
            try:
                # Run RAG workflow with conversation context
                # The workflow expects conversation_history as the second parameter
                result = self.rag_workflow.run(user_query, conversation_history)
                
                # The answer includes the link directly from the LLM
                response = result['answer']
                
                # Add AI response to messages
                state["messages"].append(AIMessage(content=response))
                print(f"✅ RAG search completed successfully")
            except Exception as e:
                print(f"⚠️  Error in RAG workflow: {e}")
                import traceback
                traceback.print_exc()
                state["messages"].append(AIMessage(
                    content="Beklager, der opstod en fejl ved søgning i databasen. Prøv venligst igen. 💙"
                ))
        
        return state


# Create agent executor (compatible with LangServe)
def create_agent():
    """Create and return the agent executor"""
    agent = KKUCAgent()
    return agent.graph


# Global agent instance
agent_executor = create_agent()
