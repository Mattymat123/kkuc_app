"""
Configuration for KKUC Ingestion Pipeline
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from backend directory
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Configuration class for ingestion pipeline"""
    
    # API Keys
    FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    COHERE_API_KEY = os.getenv("COHERE_API_KEY")
    WEAVIATE_URL = os.getenv("WEAVIATE_URL")
    WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
    
    # Target website
    TARGET_URL = "https://kkuc.dk"
    
    # Firecrawl settings
    FIRECRAWL_MAX_PAGES = 100  # Maximum pages to crawl (set to reasonable limit)
    FIRECRAWL_FORMATS = ['markdown', 'html']
    
    # Claude settings (via OpenRouter)
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    CLAUDE_CHUNKING_MODEL = "anthropic/claude-haiku-4.5"  # Haiku 4.5 for semantic chunking
    CLAUDE_CONTEXT_MODEL = "anthropic/claude-3.5-haiku"     # Latest Haiku for fast contextualization
    CLAUDE_MAX_TOKENS = 4096
    CLAUDE_TEMPERATURE = 0
    
    # Cohere settings
    COHERE_MODEL = "embed-multilingual-v3.0"  # Supports Danish
    COHERE_INPUT_TYPE = "search_document"
    
    # Weaviate settings
    WEAVIATE_CLASS_NAME = "KKUCContent"
    WEAVIATE_BATCH_SIZE = 100
    
    # Processing settings
    TEST_MODE = False  # Set to True to process only first 5 pages
    
    @classmethod
    def validate(cls):
        """Validate that all required API keys are set"""
        required_keys = [
            ("FIRECRAWL_API_KEY", cls.FIRECRAWL_API_KEY),
            ("OPENROUTER_API_KEY", cls.OPENROUTER_API_KEY),
            ("COHERE_API_KEY", cls.COHERE_API_KEY),
            ("WEAVIATE_URL", cls.WEAVIATE_URL),
            ("WEAVIATE_API_KEY", cls.WEAVIATE_API_KEY),
        ]
        
        missing = [name for name, value in required_keys if not value]
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please add them to {env_path}"
            )
        
        return True
