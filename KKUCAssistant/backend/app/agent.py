"""
Main KKUC Assistant Agent - Minimalist with Calendar Subgraph
No RAG switching during booking - booking_active flag prevents routing changes
"""
import os
from typing import TypedDict, List, Annotated, Literal, Optional, Dict, Any
from operator import add

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.workflows.rag.workflow import SimplifiedRAGWorkflow
from app.workflows.calendar.workflow import CalendarSubgraph

load_dotenv()


class AgentState(TypedDict):
    """State for KKUC agent"""
    messages: Annotated[List[BaseMessage], add]
    booking_active: bool
    booking_context: Optional[Dict[str, Any]]


class KKUCAgent:
    """Main agent with calendar subgraph and RAG workflow"""
    
    def __init__(self):
        self.calendar_workflow = CalendarSubgraph()
        self.rag_workflow = SimplifiedRAGWorkflow()
        self.llm = ChatOpenAI(
            model="anthropic/claude-haiku-4.5",
            temperature=0,
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1"
        )
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build agent graph with routing"""
        workflow = StateGraph(AgentState)
        
        workflow.add_node("route", self.route_node)
        workflow.add_node("calendar", self.calendar_node)
        workflow.add_node("rag", self.rag_node)
        
        workflow.set_entry_point("route")
        workflow.add_conditional_edges(
            "route",
            self.route_decision,
            {"calendar": "calendar", "rag": "rag"}
        )
        workflow.add_edge("calendar", END)
        workflow.add_edge("rag", END)
        
        return workflow
    
    def route_node(self, state: AgentState) -> Dict[str, Any]:
        """Entry point - just passes through state without modifying it"""
        # Don't return any state updates - let the checkpointer handle state persistence
        # Returning values here could overwrite the persisted state
        return {}
    
    def route_decision(self, state: AgentState) -> Literal["calendar", "rag"]:
        """Decide between calendar or RAG"""
        
        # If booking is active, ALWAYS go to calendar (locked)
        if state.get("booking_active"):
            print(f"🔒 Booking active - routing to calendar (locked)")
            return "calendar"
        
        if not state["messages"]:
            return "rag"
        
        last_msg = state["messages"][-1]
        if not isinstance(last_msg, HumanMessage):
            return "rag"
        
        user_input = last_msg.content
        if isinstance(user_input, list):
            user_input = " ".join([
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in user_input
            ])
        
        user_input_lower = user_input.lower().strip()
        
        # Check for booking keywords
        booking_keywords = ["book", "tid", "aftale", "møde", "booking", "tirsdag", "onsdag"]
        if any(keyword in user_input_lower for keyword in booking_keywords):
            print(f"📅 Booking keyword detected - routing to calendar")
            return "calendar"
        
        # Use LLM for intent classification
        try:
            classification_prompt = f"""Du er en intent classifier.

Besked: "{user_input}"

Svar KUN med "calendar" eller "rag":
- calendar: hvis brugeren ønsker at booke en tid/aftale
- rag: hvis brugeren spørger om noget andet"""
            
            response = self.llm.invoke([HumanMessage(content=classification_prompt)])
            intent = response.content.strip().lower()
            
            if "calendar" in intent:
                print(f"📅 LLM classified as calendar intent")
                return "calendar"
            else:
                print(f"🔍 LLM classified as RAG intent")
                return "rag"
        except Exception as e:
            print(f"⚠️  LLM error: {e}, defaulting to RAG")
            return "rag"
    
    def calendar_node(self, state: AgentState) -> Dict[str, Any]:
        """Handle calendar booking - delegates to workflow"""
        try:
            # Delegate to calendar workflow (like rag_node does)
            result = self.calendar_workflow.run(state)
            return result
        except Exception as e:
            print(f"❌ Calendar error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "messages": [AIMessage(content="Beklager, der opstod en fejl. Prøv igen. 💙")],
                "booking_active": False,
                "booking_context": None
            }
    
    def rag_node(self, state: AgentState) -> Dict[str, Any]:
        """Handle RAG search"""
        if not state["messages"]:
            return {"messages": []}
        
        last_msg = state["messages"][-1]
        if not isinstance(last_msg, HumanMessage):
            return {"messages": []}
        
        user_query = last_msg.content
        if isinstance(user_query, list):
            user_query = " ".join([
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in user_query
            ])
        
        print(f"\n🔍 RAG Handler: Processing query...")
        
        try:
            history = state["messages"][:-1] if len(state["messages"]) > 1 else []
            
            result = self.rag_workflow.run(user_query, history)
            response = result.get("answer", "Beklager, jeg kunne ikke finde et svar.")
            
            return {
                "messages": [AIMessage(content=response)],
                "booking_active": False
            }
        except Exception as e:
            print(f"❌ RAG error: {e}")
            return {
                "messages": [AIMessage(content="Beklager, der opstod en fejl. Prøv igen. 💙")],
                "booking_active": False
            }


def create_agent():
    """Create agent with checkpointing"""
    agent = KKUCAgent()
    checkpointer = MemorySaver()
    return agent.graph.compile(checkpointer=checkpointer)


agent_executor = create_agent()
