"""
Simplified RAG Workflow for KKUC Assistant with LangSmith Tracing
Three-step pipeline: Query Rewriting -> Hybrid Search with Reranking -> URL Validation
"""
import os
import time
from typing import Dict, List, Optional, TypedDict, Annotated
from operator import add

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langsmith import traceable

from ..tools.rag.search_tools import SearchTools
from ..tools.rag.query_tools import QueryTools
from ..tools.rag.validation_tools import ValidationTools

load_dotenv()


class RAGState(TypedDict):
    """State for RAG workflow"""
    query: str
    rewritten_queries: List[str]
    search_results: List
    validated_url: Optional[str]
    validated_chunks: List
    answer: str
    source_url: Optional[str]
    page_title: Optional[str]
    description: Optional[str]
    messages: Annotated[List[BaseMessage], add]


class SimplifiedRAGWorkflow:
    """Simplified RAG workflow with LangSmith tracing"""
    
    def __init__(self):
        """Initialize RAG workflow with tools and LangSmith tracing"""
        # Initialize LLM for answer generation
        self.llm = ChatOpenAI(
            model="anthropic/claude-sonnet-4.5",
            temperature=0,
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1"
        )
        
        # Initialize tools
        self.search_tools = SearchTools()
        self.query_tools = QueryTools()
        self.validation_tools = ValidationTools()
        
        # System prompt for answer generation
        self.system_prompt = """Du er en hjælpsom og empatisk AI-assistent for KKUC (Københavns Kommunes Rusmiddelcenter).

Din opgave er at hjælpe brugere med spørgsmål om stofmisbrug, alkoholmisbrug og behandlingsmuligheder.

Vigtige retningslinjer:
- Svar altid på dansk
- Vær MEGET empatisk, varm og ikke-dømmende 💙
- Brug emojis for at gøre svaret mere tilgængeligt
- Fokuser DIREKTE på brugerens spørgsmål
- Hold svarene kortere og mere præcise
- Brug kun information fra den givne kontekst
- Strukturer svaret med relevante overskrifter når det giver mening"""
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the simplified 3-step RAG workflow graph"""
        workflow = StateGraph(RAGState)
        
        # Add nodes for each step
        workflow.add_node("step1_rewrite_query", self.step1_rewrite_query)
        workflow.add_node("step2_hybrid_search_rerank", self.step2_hybrid_search_rerank)
        workflow.add_node("step3_validate_and_generate", self.step3_validate_and_generate)
        
        # Define linear flow
        workflow.set_entry_point("step1_rewrite_query")
        workflow.add_edge("step1_rewrite_query", "step2_hybrid_search_rerank")
        workflow.add_edge("step2_hybrid_search_rerank", "step3_validate_and_generate")
        workflow.add_edge("step3_validate_and_generate", END)
        
        return workflow.compile()
    
    @traceable(name="Step 1: Query Rewriting")
    def step1_rewrite_query(self, state: RAGState) -> RAGState:
        """Step 1: Rewrite query for better search - single simplified version with conversation context"""
        step_start = time.time()
        print("\n🔄 Step 1: Rewriting query...")
        
        query = state["query"]
        # Get conversation history from state
        conversation_history = state.get("messages", [])
        
        if conversation_history:
            print(f"  📝 Using conversation context with {len(conversation_history)} messages")
        else:
            print(f"  ℹ️  No conversation history available")
        
        # Get single rewritten query with conversation context
        rewritten_query = self.query_tools.rewrite_single_query(query, conversation_history)
        
        # Use both original and rewritten
        state["rewritten_queries"] = [query, rewritten_query]
        
        step_time = time.time() - step_start
        print(f"  ✓ Generated simplified query variation")
        print(f"  ⏱️  Step 1 time: {step_time:.2f}s")
        
        return state
    
    @traceable(name="Step 2: Hybrid Search with Reranking")
    def step2_hybrid_search_rerank(self, state: RAGState) -> RAGState:
        """Step 2: Perform hybrid search and rerank results"""
        step_start = time.time()
        print("\n🔍 Step 2: Hybrid search with reranking...")
        
        # Perform hybrid search for each query variation
        search_start = time.time()
        all_results = []
        for query in state["rewritten_queries"]:
            results = self.search_tools.hybrid_search(query, limit=15)
            all_results.extend(results)
        search_time = time.time() - search_start
        
        # Deduplicate results
        unique_results = self._deduplicate_results(all_results)
        print(f"  ✓ Found {len(unique_results)} unique results (search: {search_time:.2f}s)")
        
        # Rerank using original query
        rerank_start = time.time()
        reranked_results = self.search_tools.rerank_results(
            state["query"], 
            unique_results, 
            top_k=15
        )
        rerank_time = time.time() - rerank_start
        
        state["search_results"] = reranked_results
        
        step_time = time.time() - step_start
        print(f"  ✓ Reranked to top {len(reranked_results)} results (rerank: {rerank_time:.2f}s)")
        print(f"  ⏱️  Step 2 time: {step_time:.2f}s")
        
        return state
    
    @traceable(name="Step 3: Answer Generation")
    def step3_validate_and_generate(self, state: RAGState) -> RAGState:
        """Step 3: Generate answer from top search results - LLM selects most relevant chunk"""
        step_start = time.time()
        print("\n✅ Step 3: Generating answer from search results...")
        
        # Check if we have any results
        if not state["search_results"]:
            state["answer"] = "Jeg kunne desværre ikke finde relevant information om dette emne på KKUC's hjemmeside."
            state["source_url"] = None
            state["page_title"] = None
            state["description"] = None
            state["validated_url"] = None
            state["validated_chunks"] = []
            print("  ✗ No search results found")
            return state
        
        # Take top 5-10 chunks (not grouped by URL yet)
        top_chunks = state["search_results"][:10]
        print(f"  ✓ Passing top {len(top_chunks)} chunks to LLM for relevance assessment")
        
        # Get conversation history from state
        conversation_history = state.get("messages", [])
        
        # Generate answer - LLM will use both chunks and conversation history
        gen_start = time.time()
        answer = self._generate_answer_with_selection(state["query"], top_chunks, conversation_history)
        gen_time = time.time() - gen_start
        
        # Answer now contains everything (link + content) or just content if no relevant source
        state["answer"] = answer
        state["source_url"] = None  # Not needed anymore, link is in answer
        state["page_title"] = None
        state["description"] = None
        state["validated_url"] = None
        state["validated_chunks"] = top_chunks
        
        step_time = time.time() - step_start
        print(f"  ✓ Answer generated successfully (generation: {gen_time:.2f}s)")
        print(f"  ⏱️  Step 3 time: {step_time:.2f}s")
        
        return state
    
    def _deduplicate_results(self, results: List) -> List:
        """Remove duplicate results based on URL and content"""
        seen = set()
        unique = []
        
        for result in results:
            key = (result.source_url, result.content[:100])
            if key not in seen:
                seen.add(key)
                unique.append(result)
        
        return unique
    
    def _group_by_url(self, results: List) -> Dict:
        """Group search results by their source URL"""
        grouped = {}
        
        for result in results:
            url = result.source_url
            if url not in grouped:
                grouped[url] = []
            grouped[url].append(result)
        
        # Sort URLs by their best chunk score
        sorted_urls = sorted(
            grouped.items(),
            key=lambda x: max(chunk.score for chunk in x[1]),
            reverse=True
        )
        
        return dict(sorted_urls[:3])  # Keep top 3 URLs
    
    @traceable(name="Generate Answer with Chunk Selection")
    def _generate_answer_with_selection(self, query: str, chunks: List, conversation_history: List[BaseMessage] = None) -> str:
        """Generate answer - LLM uses both web search chunks AND conversation history"""
        
        # Format chunks with metadata for LLM to choose from
        chunks_context = []
        for i, chunk in enumerate(chunks, 1):
            chunks_context.append(
                f"[CHUNK {i}]\n"
                f"Titel: {chunk.page_title}\n"
                f"URL: {chunk.source_url}\n"
                f"Indhold: {chunk.content}\n"
            )
        
        web_context = "\n---\n".join(chunks_context)
        
        # Format conversation history
        conversation_context = ""
        if conversation_history:
            recent_messages = conversation_history[-10:]  # Last 5 exchanges
            context_parts = []
            for msg in recent_messages:
                role = "Bruger" if isinstance(msg, HumanMessage) else "Assistent"
                context_parts.append(f"{role}: {msg.content}")
            conversation_context = "\n\n".join(context_parts)
        
        # Create prompt that instructs LLM to use BOTH sources
        prompt = f"""Du får to informationskilder:
1. Informationsstykker fra KKUC's hjemmeside (web søgning)
2. Tidligere samtalehistorik

Din opgave er at besvare brugerens spørgsmål ved at bruge BEGGE kilder:

SAMTALEHISTORIK:
{conversation_context if conversation_context else "Ingen tidligere samtale"}

WEB SØGNING - Informationsstykker fra KKUC's hjemmeside:
{web_context}

Brugerens spørgsmål: {query}

SÅDAN BESVARER DU:

1. HVIS spørgsmålet kan besvares fra SAMTALEHISTORIKKEN (f.eks. "hvad var det nummer?", "fortæl mig mere om det"):
   - Besvar DIREKTE baseret på samtalehistorikken
   - Inkluder IKKE noget link
   - Vær kort og præcis (1-2 afsnit)
   - Brug emojis 💙

2. HVIS spørgsmålet kræver NY information fra KKUC's hjemmeside:
   - Vurder om NOGEN af web chunks er relevante
   - HVIS JA: Start dit svar med linket til den MEST relevante chunk: 🔗 [Titel](URL)
   - Saml information fra ALLE relevante chunks
   - Giv et KORT, empatisk svar (2-3 afsnit) med emojis 💙
   - HVIS NEJ: Skriv "Jeg har desværre ikke information om dette emne på KKUC's hjemmeside. 💙"

3. HVIS spørgsmålet kan besvares ved at KOMBINERE begge kilder:
   - Brug information fra samtalen som kontekst
   - Tilføj ny information fra web chunks
   - Inkluder link hvis du bruger web chunks: 🔗 [Titel](URL)

KRITISK VIGTIGT - ANTI-HALLUCINATION REGLER:
- Besvar brugerens spørgsmål DIREKTE - gå lige til sagen
- Brug BÅDE samtalehistorik og web chunks når det er relevant
- Hold svaret KORT (1-3 afsnit) men informativt
- Vær empatisk og brug emojis 💙 🌟 ✨ 💪
- GENERER ALDRIG svar baseret på din egen viden - KUN fra de givne kilder
- VERIFICER at al information kommer DIREKTE fra chunks eller samtalehistorik
- Hvis du inkluderer et link, kopier URL'en PRÆCIST fra den mest relevante chunk
- OPFIND ALDRIG telefonnumre, adresser, navne eller andre fakta
- Hvis informationen ikke er i kilderne, sig ÆRLIGT at du ikke har den information
- DOBBELT-TJEK at alle fakta (numre, navne, adresser) matcher præcist med kilderne

Svar:"""

        try:
            # Stream the response for better UX
            answer_chunks = []
            for chunk in self.llm.stream([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]):
                if hasattr(chunk, 'content'):
                    answer_chunks.append(chunk.content)
            
            answer = "".join(answer_chunks).strip()
            
            # Log what sources were used
            if "🔗" in answer:
                print("  ✓ LLM used web search and included link")
            elif conversation_context:
                print("  ℹ️  LLM answered from conversation history")
            else:
                print("  ℹ️  LLM determined no relevant information available")
            
            return answer
            
        except Exception as e:
            print(f"  ⚠️  Error generating answer: {e}")
            import traceback
            traceback.print_exc()
            return "Beklager, jeg kunne ikke generere et svar. Prøv venligst igen."
    
    def _generate_description(self, chunks: List) -> str:
        """Generate a short description of the source content"""
        if not chunks:
            return ""
        
        # Use first chunk's content for description
        content = chunks[0].content[:200]
        return f"Information om {chunks[0].page_title.lower()}"
    
    @traceable(
        name="RAG Workflow",
        metadata={"metric": "time_to_first_token"}
    )
    def run(self, user_query: str, conversation_history: List[BaseMessage] = None) -> Dict[str, Optional[str]]:
        """
        Execute simplified RAG workflow with LangSmith tracing
        Returns dict with 'answer', 'source_url', 'page_title', and 'description'
        """
        start_time = time.time()
        
        print("\n" + "="*60)
        print("🚀 Starting Simplified RAG Workflow")
        print(f"⏱️  Start time: {start_time}")
        print("="*60)
        
        try:
            # Initialize state with conversation history
            initial_state = RAGState(
                query=user_query,
                rewritten_queries=[],
                search_results=[],
                validated_url=None,
                validated_chunks=[],
                answer="",
                source_url=None,
                page_title=None,
                description=None,
                messages=conversation_history or []
            )
            
            # Run the graph
            final_state = self.graph.invoke(initial_state)
            
            # Calculate time to first token (when answer generation starts)
            ttft = time.time() - start_time
            
            # Extract result
            result = {
                "answer": final_state["answer"],
                "source_url": final_state["source_url"],
                "page_title": final_state["page_title"],
                "description": final_state["description"]
            }
            
            total_time = time.time() - start_time
            
            print("\n" + "="*60)
            print("✅ RAG Workflow Complete")
            print(f"⏱️  Time to First Token (TTFT): {ttft:.2f}s")
            print(f"⏱️  Total Time: {total_time:.2f}s")
            print("="*60 + "\n")
            
            return result
            
        except Exception as e:
            print(f"\n❌ Error in RAG workflow: {e}")
            return {
                "answer": "Beklager, der opstod en fejl. Prøv venligst igen.",
                "source_url": None,
                "page_title": None,
                "description": None
            }
