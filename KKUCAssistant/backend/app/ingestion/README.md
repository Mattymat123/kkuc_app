# KKUC Ingestion Pipeline

This pipeline crawls the KKUC website, processes content into semantic chunks, and uploads to Weaviate for RAG search.

## Overview

The pipeline performs these steps:
1. **Crawl** - Uses Firecrawl to crawl all pages from kkuc.dk
2. **Chunk** - Uses Claude Sonnet 4.5 (via OpenRouter) to break pages into semantic chunks
3. **Contextualize** - Uses Claude 3.5 Haiku (via OpenRouter) to add context to each chunk
4. **Embed** - Uses Cohere embed-multilingual-v3.0 to generate embeddings (supports Danish)
5. **Upload** - Stores in Weaviate with hybrid search enabled

**Models Used**:
- **Chunking**: `anthropic/claude-sonnet-4.5` - Latest Sonnet for intelligent semantic chunking
- **Contextualization**: `anthropic/claude-3.5-haiku` - Fast Haiku for adding document context
- **Embeddings**: `embed-multilingual-v3.0` - Cohere's multilingual model (optimized for Danish)

## Setup

### 1. Install Dependencies

```bash
cd KKUCAssistant/backend
poetry install
```

Or with pip:
```bash
pip install firecrawl-py anthropic cohere weaviate-client
```

### 2. Configure API Keys

Add these to your `.env` file:

```bash
# OpenRouter API key (used for Claude models via OpenRouter)
OPENROUTER_API_KEY=your_key_here

# Firecrawl API key (for web crawling)
FIRECRAWL_API_KEY=your_key_here

# Cohere API key (for embeddings)
COHERE_API_KEY=your_key_here

# Weaviate Cloud credentials
WEAVIATE_URL=https://your-cluster.weaviate.network
WEAVIATE_API_KEY=your_key_here
```

**Note**: The pipeline uses the same `OPENROUTER_API_KEY` as your RAG agent, accessing Claude models through OpenRouter's API.

## Usage

### Test Mode (First 5 Pages Only)

Test the pipeline on a small subset first:

```bash
cd KKUCAssistant/backend
python -m app.ingestion.run --test
```

This will:
- Process only the first 5 pages
- Take ~5-10 minutes
- Cost ~$0.15

### Full Ingestion

Once testing is successful, run the full ingestion:

```bash
python -m app.ingestion.run
```

This will:
- Process all pages from kkuc.dk
- Take ~30-60 minutes (depending on site size)
- Cost ~$2.57 (estimated for 100 pages)

## What Gets Stored

Each chunk in Weaviate contains:

```python
{
  "content": "Original chunk text for display",
  "source_url": "https://kkuc.dk/page-url",
  "page_title": "Page Title"
}
```

Plus a vector embedding for semantic search.

## Querying the Data

After ingestion, you can query the data from your RAG agent:

```python
import weaviate

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=WEAVIATE_URL,
    auth_credentials=weaviate.auth.AuthApiKey(WEAVIATE_API_KEY)
)

collection = client.collections.get("KKUCContent")

# Semantic search
results = collection.query.near_text(
    query="alkoholbehandling",
    limit=5
)

for item in results.objects:
    print(f"Content: {item.properties['content']}")
    print(f"Source: {item.properties['source_url']}")
    print(f"Title: {item.properties['page_title']}")
    print("---")
```

## Troubleshooting

### "Missing required environment variables"
- Make sure all API keys are set in `.env`
- Check that `.env` is in the `backend/` directory
- Ensure `OPENROUTER_API_KEY` is set (same key used by your RAG agent)

### "Class 'KKUCContent' already exists"
- The pipeline will ask if you want to delete and recreate
- Type "yes" to start fresh, or "no" to append to existing data

### Firecrawl rate limits
- The pipeline handles rate limits automatically
- If you hit limits, wait a few minutes and try again

### OpenRouter/Claude API errors
- Check your OpenRouter API key is valid
- Ensure you have sufficient credits on OpenRouter
- The pipeline uses Claude Sonnet 4.5 and Claude 3.5 Haiku through OpenRouter

### Cohere API errors
- Check your Cohere API key is valid
- The free tier should be sufficient for testing

## Cost Breakdown

For ~100 pages with 7 chunks per page:

| Service | Cost |
|---------|------|
| Firecrawl crawling | $0.10 |
| Claude Sonnet (chunking) | $1.00 |
| Claude Haiku (context) | $1.40 |
| Cohere embeddings | $0.07 |
| **Total** | **~$2.57** |

## Next Steps

After ingestion is complete:
1. Create a vector search tool for your RAG agent
2. Implement query rewriting for better search
3. Add hybrid search (BM25 + vector)
4. Consider incremental updates for changed pages
