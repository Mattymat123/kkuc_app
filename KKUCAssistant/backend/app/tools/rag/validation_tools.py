"""
Validation Tools for RAG Workflow
Handles URL relevance validation
"""
import os
from typing import List, Tuple

from openai import OpenAI

from . import SearchResult


class ValidationTools:
    """Tools for validating search results and URLs"""
    
    def __init__(self):
        """Initialize validation tools with API client"""
        # Initialize OpenAI client (for Claude via OpenRouter)
        self.openai_client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
    
    def validate_url_relevance(
        self, 
        url: str, 
        chunks: List[SearchResult], 
        query: str
    ) -> Tuple[bool, float]:
        """
        Validate if a URL's content is relevant to the query
        Returns (is_relevant, confidence_score)
        """
        # Combine all chunks from this URL
        combined_content = "\n\n".join([chunk.content for chunk in chunks])
        
        # Limit content length for API call
        if len(combined_content) > 4000:
            combined_content = combined_content[:4000] + "..."
        
        prompt = f"""Du skal vurdere om indholdet fra en hjemmeside hjælper med at besvare brugerens spørgsmål.

Brugerens spørgsmål: "{query}"

Hjemmeside: {url}
Indhold:
{combined_content}

Vurder:
1. Hjælper dette indhold med at besvare spørgsmålet?
2. Hvor sikker er du? (1-10, hvor 10 er meget sikker)

Svar i dette format:
RELEVANT: JA eller NEJ
SIKKERHED: [tal 1-10]
BEGRUNDELSE: [kort forklaring]"""

        try:
            response = self.openai_client.chat.completions.create(
                model="anthropic/claude-3.5-haiku",
                max_tokens=200,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = response.choices[0].message.content.strip()
            
            # Parse response
            is_relevant = "RELEVANT: JA" in result.upper()
            
            # Extract confidence score
            confidence = 5.0  # Default
            for line in result.split('\n'):
                if 'SIKKERHED:' in line.upper():
                    try:
                        confidence = float(line.split(':')[1].strip())
                    except:
                        pass
            
            print(f"    {'✓' if is_relevant else '✗'} URL validation: {url[:50]}... (confidence: {confidence}/10)")
            
            return is_relevant, confidence
            
        except Exception as e:
            print(f"    ⚠️  Error validating URL: {e}")
            return False, 0.0
