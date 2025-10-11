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


class KKUCAgent:
    """Main KKUC Assistant Agent"""
    
    def __init__(self):
        """Initialize the agent with workflows"""
        # Initialize workflows
        self.rag_workflow = SimplifiedRAGWorkflow()
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the main agent graph - always uses RAG with conversation context"""
        workflow = StateGraph(AgentState)
        
        # Add single node for RAG search
        workflow.add_node("rag_search", self.rag_search_node)
        
        # Simple linear flow
        workflow.set_entry_point("rag_search")
        workflow.add_edge("rag_search", END)
        
        # Enable streaming for the graph
        return workflow.compile()
    
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
