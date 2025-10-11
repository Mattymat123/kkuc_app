"""
Main KKUC Assistant Agent
Orchestrates different workflows (RAG, etc.) using LangGraph
Compatible with LangServe deployment
"""
import os
from typing import TypedDict, List, Annotated, Literal
from operator import add

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END

from .workflows.simplified_rag_workflow import SimplifiedRAGWorkflow

load_dotenv()


class AgentState(TypedDict):
    """State for KKUC agent - compatible with LangServe"""
    messages: Annotated[List[BaseMessage], add]
    needs_rag: bool  # Whether RAG search is needed


class KKUCAgent:
    """Main KKUC Assistant Agent"""
    
    def __init__(self):
        """Initialize the agent with workflows"""
        # Initialize LLM for routing and direct answers
        self.llm = ChatOpenAI(
            model="anthropic/claude-sonnet-4.5",
            temperature=0,
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1"
        )
        
        # Initialize lightweight LLM for routing decisions
        self.router_llm = ChatOpenAI(
            model="openai/gpt-4o-mini",
            temperature=0,
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1"
        )
        
        # Initialize workflows
        self.rag_workflow = SimplifiedRAGWorkflow()
        
        # Build the graph
        self.graph = self._build_graph()
        
        # System prompt for direct answers
        self.system_prompt = """Du er en hjælpsom AI-assistent for KKUC (Københavns Kommunes Rusmiddelcenter).

Din opgave er at hjælpe brugere med spørgsmål om stofmisbrug, alkoholmisbrug og behandlingsmuligheder.

Vigtige retningslinjer:
- Svar altid på dansk
- Vær empatisk og ikke-dømmende
- Brug information fra samtalehistorikken når det er relevant
- Vær kort og præcis i dine svar
- Brug emojis for at gøre svaret mere tilgængeligt 💙"""
    
    def _build_graph(self) -> StateGraph:
        """Build the main agent graph with intelligent routing"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("route_query", self.route_query_node)
        workflow.add_node("answer_from_context", self.answer_from_context_node)
        workflow.add_node("rag_search", self.rag_search_node)
        
        # Define flow with conditional routing
        workflow.set_entry_point("route_query")
        workflow.add_conditional_edges(
            "route_query",
            self.should_use_rag,
            {
                "rag": "rag_search",
                "direct": "answer_from_context"
            }
        )
        workflow.add_edge("answer_from_context", END)
        workflow.add_edge("rag_search", END)
        
        # Enable streaming for the graph
        return workflow.compile()
    
    def should_use_rag(self, state: AgentState) -> Literal["rag", "direct"]:
        """Determine if RAG search is needed based on routing decision"""
        return "rag" if state.get("needs_rag", True) else "direct"
    
    def route_query_node(self, state: AgentState) -> AgentState:
        """Decide whether to use RAG or answer from conversation context"""
        last_message = state["messages"][-1]
        
        if not isinstance(last_message, HumanMessage):
            state["needs_rag"] = False
            return state
        
        user_query = last_message.content
        conversation_history = state["messages"][:-1] if len(state["messages"]) > 1 else []
        
        # Build conversation context for routing decision
        context = ""
        if conversation_history:
            recent_messages = conversation_history[-6:]  # Last 3 exchanges
            context_parts = []
            for msg in recent_messages:
                role = "Bruger" if isinstance(msg, HumanMessage) else "Assistent"
                content = msg.content[:300] if len(msg.content) > 300 else msg.content
                context_parts.append(f"{role}: {content}")
            context = "\n".join(context_parts)
        
        # Use LLM to decide if RAG is needed
        routing_prompt = f"""Du er en routing-assistent der beslutter om et spørgsmål kan besvares fra samtalehistorikken eller kræver søgning i KKUC's database.

Samtalehistorik:
{context if context else "Ingen tidligere samtale"}

Nuværende spørgsmål: "{user_query}"

Analyser om spørgsmålet:
1. Kan besvares DIREKTE fra samtalehistorikken (f.eks. "hvad er hans nummer?" når nummeret lige er nævnt)
2. Er en simpel opfølgning der refererer til information i samtalen
3. Kræver ny information fra KKUC's database

Svar KUN med "DIRECT" hvis spørgsmålet kan besvares fra samtalehistorikken.
Svar "RAG" hvis der skal søges i databasen.

Eksempler:
- "hvad er hans nummer?" efter at have talt om en person → DIRECT
- "hvem er direktøren?" → RAG (ny information)
- "fortæl mere om det" efter et svar → DIRECT hvis kontekst er klar, ellers RAG
- "hvad er åbningstiderne?" → RAG (specifik information)

Dit svar (kun DIRECT eller RAG):"""

        try:
            response = self.router_llm.invoke([
                HumanMessage(content=routing_prompt)
            ])
            
            decision = response.content.strip().upper()
            state["needs_rag"] = decision == "RAG"
            
            print(f"\n🔀 Routing decision: {'RAG search' if state['needs_rag'] else 'Direct answer from context'}")
            
        except Exception as e:
            print(f"⚠️  Error in routing: {e}, defaulting to RAG")
            state["needs_rag"] = True
        
        return state
    
    def answer_from_context_node(self, state: AgentState) -> AgentState:
        """Answer question directly from conversation context without RAG"""
        last_message = state["messages"][-1]
        user_query = last_message.content
        conversation_history = state["messages"][:-1]
        
        # Build context for answer
        context_parts = []
        for msg in conversation_history[-10:]:  # Last 5 exchanges
            role = "Bruger" if isinstance(msg, HumanMessage) else "Assistent"
            context_parts.append(f"{role}: {msg.content}")
        context = "\n\n".join(context_parts)
        
        answer_prompt = f"""Baseret på samtalehistorikken, besvar brugerens spørgsmål kort og præcist.

Samtalehistorik:
{context}

Brugerens spørgsmål: {user_query}

Vigtige retningslinjer:
- Besvar DIREKTE baseret på information i samtalehistorikken
- Vær kort og præcis (1-2 sætninger)
- Brug emojis for at gøre svaret mere tilgængeligt 💙
- Hvis spørgsmålet refererer til noget specifikt (hans, hendes, det), brug den konkrete information fra samtalen

Dit svar:"""

        try:
            # Stream the response - LangGraph will handle the streaming
            answer_chunks = []
            for chunk in self.llm.stream([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=answer_prompt)
            ]):
                if hasattr(chunk, 'content'):
                    answer_chunks.append(chunk.content)
            
            answer = "".join(answer_chunks)
            state["messages"].append(AIMessage(content=answer))
            print("✅ Answered directly from conversation context")
            
        except Exception as e:
            print(f"⚠️  Error generating direct answer: {e}")
            import traceback
            traceback.print_exc()
            state["messages"].append(AIMessage(
                content="Beklager, jeg kunne ikke behandle dit spørgsmål. Prøv venligst igen. 💙"
            ))
        
        return state
    
    def rag_search_node(self, state: AgentState) -> AgentState:
        """Process user query through RAG workflow"""
        last_message = state["messages"][-1]
        
        if isinstance(last_message, HumanMessage):
            user_query = last_message.content
            
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
