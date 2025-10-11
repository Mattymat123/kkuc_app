"""
Main Ingestion Pipeline for KKUC
Crawls website, chunks content, adds context, embeds, and uploads to Weaviate.
"""
import json
import time
from typing import List, Dict, Any
from dataclasses import dataclass

from firecrawl import FirecrawlApp
from openai import OpenAI
import cohere
import weaviate
from weaviate.classes.config import Configure, Property, DataType

from .config import Config


@dataclass
class Page:
    """Represents a crawled page"""
    url: str
    title: str
    content: str


@dataclass
class Chunk:
    """Represents a semantic chunk of content"""
    text: str
    topic: str
    page_url: str
    page_title: str
    index: int


@dataclass
class EnrichedChunk:
    """Chunk with context and embedding"""
    original_text: str
    contextualized_text: str
    embedding: List[float]
    page_url: str
    page_title: str
    chunk_index: int


class IngestionPipeline:
    """Main pipeline for ingesting KKUC content into Weaviate"""
    
    def __init__(self, config: Config):
        """Initialize pipeline with API clients"""
        self.config = config
        
        # Validate configuration
        config.validate()
        
        # Initialize API clients
        self.firecrawl = FirecrawlApp(api_key=config.FIRECRAWL_API_KEY)
        self.openai_client = OpenAI(
            api_key=config.OPENROUTER_API_KEY,
            base_url=config.OPENROUTER_BASE_URL
        )
        self.cohere_client = cohere.Client(api_key=config.COHERE_API_KEY)
        
        # Initialize Weaviate client
        self.weaviate_client = weaviate.connect_to_weaviate_cloud(
            cluster_url=config.WEAVIATE_URL,
            auth_credentials=weaviate.auth.AuthApiKey(config.WEAVIATE_API_KEY)
        )
        
        # Stats tracking
        self.stats = {
            'pages_crawled': 0,
            'chunks_created': 0,
            'chunks_uploaded': 0,
            'total_cost': 0.0
        }
    
    def crawl_website(self) -> List[Page]:
        """Crawl entire website using Firecrawl"""
        print(f"🕷️  Crawling {self.config.TARGET_URL}...")
        
        try:
            # Use Firecrawl's crawl endpoint
            crawl_result = self.firecrawl.crawl_url(
                self.config.TARGET_URL,
                params={
                    'limit': self.config.FIRECRAWL_MAX_PAGES,
                    'scrapeOptions': {
                        'formats': self.config.FIRECRAWL_FORMATS
                    }
                },
                poll_interval=5
            )
            
            # Extract pages from result
            pages = []
            if crawl_result and 'data' in crawl_result:
                for item in crawl_result['data']:
                    if 'markdown' in item and item['markdown']:
                        page = Page(
                            url=item.get('metadata', {}).get('sourceURL', item.get('url', '')),
                            title=item.get('metadata', {}).get('title', 'Untitled'),
                            content=item['markdown']
                        )
                        pages.append(page)
            
            self.stats['pages_crawled'] = len(pages)
            print(f"✅ Crawled {len(pages)} pages")
            
            # If in test mode, only return first 5 pages
            if self.config.TEST_MODE:
                print("⚠️  TEST MODE: Processing only first 5 pages")
                pages = pages[:5]
            
            return pages
            
        except Exception as e:
            print(f"❌ Error crawling website: {e}")
            raise
    
    def chunk_page(self, page: Page) -> List[Chunk]:
        """Break page into semantic chunks using Claude"""
        print(f"  📄 Chunking: {page.title}")
        
        prompt = f"""Analyze this Danish webpage about substance abuse treatment.

Page Title: {page.title}
Content:
{page.content[:8000]}

Break this into semantic chunks where each chunk:
1. Covers ONE complete topic (e.g., "treatment programs", "contact info", "eligibility")
2. Is self-contained and understandable alone
3. Is 200-500 words
4. Preserves all key details

Return ONLY a JSON array (no other text):
[
  {{"chunk_text": "...", "topic": "..."}},
  ...
]"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.config.CLAUDE_CHUNKING_MODEL,
                max_tokens=self.config.CLAUDE_MAX_TOKENS,
                temperature=self.config.CLAUDE_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract JSON from response
            response_text = response.choices[0].message.content
            
            # Try to find JSON array in response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx == -1 or end_idx == 0:
                print(f"  ⚠️  No JSON found, creating single chunk")
                return [Chunk(
                    text=page.content[:1000],
                    topic="Full page",
                    page_url=page.url,
                    page_title=page.title,
                    index=0
                )]
            
            json_str = response_text[start_idx:end_idx]
            chunks_data = json.loads(json_str)
            
            # Create Chunk objects
            chunks = []
            for i, chunk_data in enumerate(chunks_data):
                chunk = Chunk(
                    text=chunk_data.get('chunk_text', ''),
                    topic=chunk_data.get('topic', 'Unknown'),
                    page_url=page.url,
                    page_title=page.title,
                    index=i
                )
                chunks.append(chunk)
            
            self.stats['chunks_created'] += len(chunks)
            self.stats['total_cost'] += 0.01  # Approximate cost per page
            
            print(f"    ✓ Created {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            print(f"  ⚠️  Error chunking page: {e}")
            # Fallback: create single chunk
            return [Chunk(
                text=page.content[:1000],
                topic="Full page",
                page_url=page.url,
                page_title=page.title,
                index=0
            )]
    
    def add_context(self, chunk: Chunk, full_page_content: str) -> str:
        """Add context to chunk using Claude Haiku"""
        prompt = f"""Document: {chunk.page_title}
Full content (first 2000 chars): {full_page_content[:2000]}...

Chunk: {chunk.text}

Write 1-2 sentences in Danish explaining what this chunk discusses in the context of the full document. Be specific about the topic."""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.config.CLAUDE_CONTEXT_MODEL,
                max_tokens=200,
                temperature=self.config.CLAUDE_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}]
            )
            
            context = response.choices[0].message.content.strip()
            self.stats['total_cost'] += 0.002  # Approximate cost per chunk
            
            return f"{context}\n\n{chunk.text}"
            
        except Exception as e:
            print(f"    ⚠️  Error adding context: {e}")
            return chunk.text
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Cohere"""
        try:
            response = self.cohere_client.embed(
                texts=texts,
                model=self.config.COHERE_MODEL,
                input_type=self.config.COHERE_INPUT_TYPE
            )
            
            self.stats['total_cost'] += len(texts) * 0.0001  # Approximate cost
            
            return response.embeddings
            
        except Exception as e:
            print(f"    ⚠️  Error generating embeddings: {e}")
            raise
    
    def setup_weaviate_schema(self):
        """Create Weaviate schema if it doesn't exist"""
        print("🗄️  Setting up Weaviate schema...")
        
        try:
            # Check if class already exists
            if self.weaviate_client.collections.exists(self.config.WEAVIATE_CLASS_NAME):
                print(f"  ⚠️  Class '{self.config.WEAVIATE_CLASS_NAME}' already exists")
                
                # Ask user if they want to delete and recreate
                response = input("  Delete and recreate? (yes/no): ")
                if response.lower() == 'yes':
                    self.weaviate_client.collections.delete(self.config.WEAVIATE_CLASS_NAME)
                    print("  ✓ Deleted existing class")
                else:
                    print("  ✓ Using existing class")
                    return
            
            # Create new class
            self.weaviate_client.collections.create(
                name=self.config.WEAVIATE_CLASS_NAME,
                description="Semantic chunks from KKUC website",
                properties=[
                    Property(
                        name="content",
                        data_type=DataType.TEXT,
                        description="Original chunk text for display"
                    ),
                    Property(
                        name="source_url",
                        data_type=DataType.TEXT,
                        description="URL of source page"
                    ),
                    Property(
                        name="page_title",
                        data_type=DataType.TEXT,
                        description="Title of source page"
                    ),
                ],
                vectorizer_config=Configure.Vectorizer.none()  # We provide vectors manually
            )
            
            print(f"  ✅ Created class '{self.config.WEAVIATE_CLASS_NAME}'")
            
        except Exception as e:
            print(f"  ❌ Error setting up schema: {e}")
            raise
    
    def upload_to_weaviate(self, enriched_chunks: List[EnrichedChunk]):
        """Upload enriched chunks to Weaviate"""
        print(f"  📤 Uploading {len(enriched_chunks)} chunks to Weaviate...")
        
        try:
            collection = self.weaviate_client.collections.get(self.config.WEAVIATE_CLASS_NAME)
            
            # Batch upload
            with collection.batch.dynamic() as batch:
                for chunk in enriched_chunks:
                    batch.add_object(
                        properties={
                            "content": chunk.original_text,
                            "source_url": chunk.page_url,
                            "page_title": chunk.page_title
                        },
                        vector=chunk.embedding
                    )
            
            self.stats['chunks_uploaded'] += len(enriched_chunks)
            print(f"    ✅ Uploaded {len(enriched_chunks)} chunks")
            
        except Exception as e:
            print(f"    ❌ Error uploading to Weaviate: {e}")
            raise
    
    def run(self):
        """Run the complete ingestion pipeline"""
        print("\n" + "="*60)
        print("🚀 KKUC INGESTION PIPELINE")
        print("="*60 + "\n")
        
        start_time = time.time()
        
        try:
            # Step 1: Setup Weaviate schema
            self.setup_weaviate_schema()
            print()
            
            # Step 2: Crawl website
            pages = self.crawl_website()
            print()
            
            # Step 3: Process each page
            print(f"📝 Processing {len(pages)} pages...\n")
            
            for i, page in enumerate(pages, 1):
                print(f"[{i}/{len(pages)}] {page.title}")
                
                # Chunk the page
                chunks = self.chunk_page(page)
                
                # Add context to each chunk
                print(f"  🔗 Adding context to {len(chunks)} chunks...")
                contextualized_texts = []
                for chunk in chunks:
                    contextualized_text = self.add_context(chunk, page.content)
                    contextualized_texts.append(contextualized_text)
                
                # Generate embeddings for all chunks at once
                print(f"  🧮 Generating embeddings...")
                embeddings = self.embed_texts(contextualized_texts)
                
                # Create enriched chunks
                enriched_chunks = []
                for chunk, contextualized_text, embedding in zip(chunks, contextualized_texts, embeddings):
                    enriched_chunk = EnrichedChunk(
                        original_text=chunk.text,
                        contextualized_text=contextualized_text,
                        embedding=embedding,
                        page_url=chunk.page_url,
                        page_title=chunk.page_title,
                        chunk_index=chunk.index
                    )
                    enriched_chunks.append(enriched_chunk)
                
                # Upload to Weaviate
                self.upload_to_weaviate(enriched_chunks)
                print()
            
            # Print final stats
            elapsed_time = time.time() - start_time
            print("="*60)
            print("✅ INGESTION COMPLETE!")
            print(f"📊 Statistics:")
            print(f"  • Pages crawled: {self.stats['pages_crawled']}")
            print(f"  • Chunks created: {self.stats['chunks_created']}")
            print(f"  • Chunks uploaded: {self.stats['chunks_uploaded']}")
            print(f"  • Estimated cost: ${self.stats['total_cost']:.2f}")
            print(f"  • Time elapsed: {elapsed_time/60:.1f} minutes")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"\n❌ Pipeline failed: {e}")
            raise
        
        finally:
            # Close Weaviate connection
            self.weaviate_client.close()
