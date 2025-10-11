"""
RAG Workflow for KKUC Assistant
Implements query rewriting, hybrid search, reranking, and URL validation
"""
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..tools.rag.search_tools import SearchTools
from ..tools.rag.query_tools import QueryTools
from ..tools.rag.validation_tools import ValidationTools

load_dotenv()


class RAGWorkflow:
    """RAG workflow for retrieving and validating information"""
    
    def __init__(self):
        """Initialize RAG workflow with tools"""
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
        self.system_prompt = """Du er en hjælpsom AI-assistent for KKUC (Københavns Kommunes Rusmiddelcenter).

Din opgave er at hjælpe brugere med spørgsmål om stofmisbrug, alkoholmisbrug og behandlingsmuligheder.

Vigtige retningslinjer:
- Svar altid på dansk
- Vær empatisk og ikke-dømmende
- Brug kun information fra den givne kontekst
- Hold svaret MEGET kort (1-2 sætninger)"""
    
    def run(self, user_query: str) -> Dict[str, Optional[str]]:
        """
        Execute RAG workflow
        Returns dict with 'answer', 'source_url', 'page_title', and 'description'
        """
        print("\n🔍 Søger i KKUC's database...")
        
        try:
            # Step 1: Rewrite query
            rewritten_queries = self.query_tools.rewrite_query(user_query)
            
            # Step 2: Hybrid search
            all_results = []
            for query in rewritten_queries:
                results = self.search_tools.hybrid_search(query, limit=15)
                all_results.extend(results)
            
            # Deduplicate
            unique_results = self._deduplicate_results(all_results)
            
            # Step 3: Rerank
            reranked_results = self.search_tools.rerank_results(
                user_query, unique_results, top_k=15
            )
            
            # Step 4: Group by URL
            grouped_urls = self._group_by_url(reranked_results)
            
            # Step 5: Validate URLs
            validated_url, validated_chunks = self._validate_urls(
                user_query, grouped_urls
            )
            
            # Step 6: Generate answer or return no info
            if validated_url:
                answer = self._generate_answer(
                    user_query, validated_url, validated_chunks
                )
                
                # Get page title and description
                page_title = validated_chunks[0].page_title if validated_chunks else "KKUC Information"
                description = self._generate_description(validated_chunks)
                
                result = {
                    "answer": answer,
                    "source_url": validated_url,
                    "page_title": page_title,
                    "description": description
                }
            else:
                result = {
                    "answer": "**Ingen relevant information fundet**\n\nJeg kunne desværre ikke finde information om dette emne på KKUC's hjemmeside. Du er velkommen til at:\n\n• Omformulere dit spørgsmål\n• Kontakte KKUC direkte for personlig rådgivning\n• Besøge deres hjemmeside for mere information",
                    "source_url": None,
                    "page_title": None,
                    "description": None
                }
            
            return result
            
        except Exception as e:
            print(f"\n❌ Error in RAG workflow: {e}")
            return {
                "answer": "Beklager, der opstod en fejl. Prøv venligst igen.",
                "source_url": None
            }
    
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
    
    def _validate_urls(self, query: str, grouped_urls: Dict) -> tuple:
        """
        Validate top URLs and return first relevant one
        Returns (url, chunks) or (None, [])
        """
        for url, chunks in grouped_urls.items():
            print(f"\n  Checking: {url}")
            
            is_relevant, confidence = self.validation_tools.validate_url_relevance(
                url, chunks, query
            )
            
            # Accept if relevant and confidence >= 7
            if is_relevant and confidence >= 7.0:
                print(f"  ✓ Found relevant URL with confidence {confidence}/10")
                return url, chunks
        
        print("  ✗ No relevant URLs found")
        return None, []
    
    def _generate_answer(self, query: str, url: str, chunks: List) -> str:
        """Generate answer using validated URL's chunks"""
        # Combine chunks for context
        context = "\n\n".join([
            f"[Fra {chunk.page_title}]\n{chunk.content}"
            for chunk in chunks
        ])
        
        # Limit context length
        if len(context) > 6000:
            context = context[:6000] + "\n\n[...indhold afkortet...]"
        
        prompt = f"""Baseret på følgende information fra KKUC's hjemmeside, besvar brugerens spørgsmål.

Brugerens spørgsmål: {query}

Relevant information fra {url}:
{context}

Svar:"""

        try:
            response = self.llm.invoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ])
            
            answer = response.content.strip()
            print("  ✓ Answer generated")
            return answer
            
        except Exception as e:
            print(f"  ⚠️  Error generating answer: {e}")
            return "Beklager, jeg kunne ikke generere et svar. Prøv venligst igen."
    
    def _generate_description(self, chunks: List) -> str:
        """Generate a short description of the source content"""
        if not chunks:
            return ""
        
        # Use first chunk's content for description
        content = chunks[0].content[:200]
        return f"Information om {chunks[0].page_title.lower()}"
