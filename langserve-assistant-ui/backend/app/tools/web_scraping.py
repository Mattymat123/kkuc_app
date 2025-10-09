import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.tools import tool
from firecrawl import FirecrawlApp

# Load .env file from backend directory (3 levels up from this file)
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

@tool
def web_scrape(query: str) -> str:
    """Scrape the KKUC website for information. Use this to search for content on kkuc.dk. 
    The query parameter should describe what information you're looking for (e.g., 'alkoholbehandling', 'stofmisbrug', 'behandlingstilbud', 'direktør', etc.).
    This tool will return relevant pages with their URLs and content that you can use to answer the user's question."""
    
    base_url = "https://kkuc.dk"
    
    # Get API key
    api_key = os.getenv("FIRECRAWL_API_KEY")
    
    if not api_key:
        return "Fejl: FIRECRAWL_API_KEY er ikke konfigureret. Kontakt administrator."
    
    try:
        # Initialize Firecrawl client
        app = FirecrawlApp(api_key=api_key)
        
        # Use v1 API to scrape the main page
        print(f"Scraping {base_url} for query: {query}")
        result = app.scrape_url(base_url, params={'formats': ['markdown']})
        
        if not result or 'markdown' not in result:
            return f"Kunne ikke hente data fra KKUC. Besøg {base_url} for information."
        
        # Get page info
        title = result.get('metadata', {}).get('title', 'KKUC')
        content = result.get('markdown', '')[:1500]
        
        # Format output
        output = f"Her er information fra KKUC om '{query}':\n\n"
        output += f"**{title}**\n"
        output += f"Link: {base_url}\n\n"
        output += f"Indhold:\n{content}...\n\n"
        output += f"For mere detaljeret information, besøg: {base_url}"
        
        return output
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error in web_scrape: {error_msg}")
        
        # Check for rate limit errors
        if 'rate limit' in error_msg.lower() or 'concurrency' in error_msg.lower():
            return f"Firecrawl API rate limit nået. Prøv igen om lidt.\n\nI mellemtiden, besøg {base_url} for information om {query}."
        
        return f"Fejl ved scraping af KKUC: {error_msg}\n\nBesøg {base_url} for information om {query}."
