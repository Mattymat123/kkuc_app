"""
Query Tools for RAG Workflow
Handles query rewriting and optimization
"""
import os
from typing import List

from openai import OpenAI


class QueryTools:
    """Tools for query processing and rewriting"""
    
    def __init__(self):
        """Initialize query tools with API client"""
        # Initialize OpenAI client (for Claude via OpenRouter)
        self.openai_client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
    
    def rewrite_query(self, query: str) -> List[str]:
        """
        Rewrite user query into multiple variations for better retrieval
        Returns list of query variations including original
        """
        prompt = f"""Du er en ekspert i at omformulere søgeforespørgsler på dansk.

Brugerens spørgsmål: "{query}"

Generer 2-3 alternative måder at formulere dette spørgsmål på, der kan hjælpe med at finde relevant information om stofmisbrug og behandling.

Returner kun forespørgslerne, en per linje, uden nummerering eller forklaring."""

        try:
            response = self.openai_client.chat.completions.create(
                model="anthropic/claude-3.5-haiku",
                max_tokens=200,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            rewrites = response.choices[0].message.content.strip().split('\n')
            rewrites = [q.strip() for q in rewrites if q.strip()]
            
            # Always include original query
            all_queries = [query] + rewrites
            
            print(f"  🔄 Query rewrites: {len(all_queries)} variations")
            return all_queries
            
        except Exception as e:
            print(f"  ⚠️  Error rewriting query: {e}")
            return [query]
    
    def rewrite_single_query(self, query: str, conversation_history: List = None) -> str:
        """
        Rewrite user query into a single simplified version for better search
        Takes conversation history into account for context
        Uses faster, lightweight model (GPT-4o-mini via OpenRouter)
        """
        # Ensure query is a string
        if isinstance(query, list):
            query = query[0] if query else ""
        
        # Build context from conversation history
        context = ""
        if conversation_history and len(conversation_history) > 0:
            # Get last few messages for context
            recent_messages = conversation_history[-6:]  # Last 3 exchanges (user + assistant)
            context_parts = []
            for msg in recent_messages:
                # Handle different message types
                if hasattr(msg, 'type'):
                    role = "Bruger" if msg.type == "human" else "Assistent"
                elif msg.__class__.__name__ == "HumanMessage":
                    role = "Bruger"
                elif msg.__class__.__name__ == "AIMessage":
                    role = "Assistent"
                else:
                    role = "Message"
                
                content = msg.content if hasattr(msg, 'content') else str(msg)
                # Limit length but keep enough context
                content_preview = content[:300] if len(content) > 300 else content
                context_parts.append(f"{role}: {content_preview}")
            context = "\n".join(context_parts)
        
        if context:
            prompt = f"""Du er en ekspert i at omformulere søgeforespørgsler til websøgning baseret på samtalehistorik.

Samtalehistorik:
{context}

Nuværende bruger-spørgsmål: "{query}"

DIN OPGAVE:
1. ANALYSER samtalehistorikken for at forstå den AFLEDTE KONTEKST af brugerens spørgsmål
2. IDENTIFICER hvad brugeren EGENTLIG spørger om baseret på samtaleforløbet
3. OMFORMULER spørgsmålet til en OPTIMAL websøgning der:
   - Erstatter ALLE pronominer (hans, hendes, det, den, dem) med konkrete navne/ting fra samtalen
   - Inkluderer RELEVANT kontekst fra samtalen der gør søgningen mere præcis
   - Er formuleret som en KLAR, SPECIFIK søgeforespørgsel
   - Fokuserer på den AFLEDTE BETYDNING af brugerens spørgsmål

EKSEMPLER:
- Samtale om "direktør Nicolai Halberg" → Spørgsmål: "hvad er hans nummer?" → Omskrivning: "Nicolai Halberg telefonnummer kontaktoplysninger"
- Samtale om "behandlingstilbud" → Spørgsmål: "hvor kan jeg få det?" → Omskrivning: "hvor kan jeg få behandling for stofmisbrug KKUC"
- Samtale om "åbningstider" → Spørgsmål: "hvad med weekenden?" → Omskrivning: "KKUC åbningstider weekend lørdag søndag"

KRITISK: Fokuser på den AFLEDTE KONTEKST - hvad brugeren EGENTLIG mener baseret på samtaleforløbet.

Returner KUN den omformulerede søgeforespørgsel, ingen forklaring:"""
        else:
            prompt = f"""Omformuler denne søgeforespørgsel til en optimal websøgning på dansk.

Original: "{query}"

Gør søgningen klar og specifik for KKUC's hjemmeside.

Returner kun den omformulerede forespørgsel, ingen forklaring:"""

        try:
            response = self.openai_client.chat.completions.create(
                model="openai/gpt-4o-mini",
                max_tokens=100,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            rewritten = response.choices[0].message.content.strip()
            
            # Ensure we return a string, not a list
            if isinstance(rewritten, list):
                rewritten = rewritten[0] if rewritten else query
            
            print(f"  🔄 Simplified query: '{rewritten}'")
            if context:
                print(f"  📝 Used conversation context from {len(recent_messages)} previous messages")
            return str(rewritten)  # Ensure it's a string
            
        except Exception as e:
            print(f"  ⚠️  Error rewriting query: {e}")
            return str(query)  # Ensure it's a string
