# KKUC RAG Agent Documentation

## Overview

The KKUC RAG (Retrieval-Augmented Generation) Agent is an advanced question-answering system that uses your ingested KKUC content to provide accurate, source-backed answers in Danish.

## Architecture

### Pipeline Flow

```
User Query
    ↓
1. Query Rewriting (Claude Haiku)
   - Generates 2-3 alternative query formulations
   - Improves retrieval recall
    ↓
2. Hybrid Search
   - Vector Search (Cohere embeddings + Weaviate)
   - BM25 Keyword Search (rank-bm25)
   - Combines both for comprehensive results
    ↓
3. Reranking (Cohere Rerank Multilingual v3.0)
   - Scores all results for relevance
   - Returns top 15 most relevant chunks
    ↓
4. URL Grouping
   - Groups chunks by source URL
   - Ranks URLs by best chunk score
   - Selects top 3 candidate URLs
    ↓
5. URL Validation (Claude Haiku)
   - Iterates through top 3 URLs
   - For each URL, validates if content answers query
   - Stops at first relevant URL (confidence ≥ 7/10)
   - If no relevant URL found → Returns "no info" message
    ↓
6. Answer Generation (Claude Sonnet 4.5)
   - Uses validated URL's chunks as context
   - Generates empathetic, accurate answer in Danish
   - Returns answer + single source URL
```

## Key Features

### 1. Context Understanding
- Already implemented in ingestion pipeline
- Each chunk has contextual information added via Claude

### 2. Query Rewriting
- Generates multiple query variations
- Improves retrieval recall
- Handles different ways users might ask the same question

### 3. Hybrid Search
- **Vector Search**: Semantic similarity using Cohere multilingual embeddings
- **BM25 Search**: Keyword matching for exact terms
- Combines both approaches for comprehensive coverage

### 4. Reranking
- Uses Cohere's rerank-multilingual-v3.0
- Optimized for Danish language
- Scores all results for true relevance

### 5. URL Validation
- Critical quality control step
- Validates actual webpage content, not just chunks
- Ensures returned URLs genuinely answer the question
- Confidence scoring (1-10) with threshold of 7

### 6. Single URL Output
- Returns exactly ONE validated source URL
- Prevents information overload
- Enables future auto-redirect functionality

## Files Structure

```
backend/app/
├── rag_agent.py           # Main RAG agent with LangGraph
├── tools/
│   ├── rag_tools.py       # RAG toolkit (search, rerank, validate)
│   └── web_scraping.py    # Existing web scraping tool
├── server.py              # FastAPI server with RAG endpoint
└── test_rag.py            # Test script for RAG agent
```

## API Usage

### Endpoint: POST `/rag/query`

**Request:**
```json
{
  "query": "Hvad er behandlingsmulighederne for stofmisbrug?"
}
```

**Response:**
```json
{
  "answer": "KKUC tilbyder ambulant behandling for stofmisbrug...",
  "source_url": "https://kkuc.dk/behandling"
}
```

**Response (No Info):**
```json
{
  "answer": "KKUC har desværre ikke information om dette emne på deres hjemmeside...",
  "source_url": null
}
```

## Testing

### Run Test Script

```bash
cd KKUCAssistant/backend
poetry run python -m app.test_rag
```

This will test the RAG agent with 5 sample queries in Danish.

### Manual Testing via API

1. Start the server:
```bash
cd KKUCAssistant/backend
poetry run uvicorn app.server:app --reload
```

2. Test via curl:
```bash
curl -X POST "http://localhost:8000/rag/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Hvad er behandlingsmulighederne?"}'
```

3. Or use the interactive docs at: `http://localhost:8000/docs`

## Configuration

### Environment Variables Required

```env
# Weaviate
WEAVIATE_URL=your_weaviate_url
WEAVIATE_API_KEY=your_weaviate_key

# OpenRouter (for Claude)
OPENROUTER_API_KEY=your_openrouter_key

# Cohere
COHERE_API_KEY=your_cohere_key
```

### Models Used

- **Query Rewriting**: Claude 3.5 Haiku (fast, cheap)
- **URL Validation**: Claude 3.5 Haiku (fast, cheap)
- **Answer Generation**: Claude Sonnet 4.5 (high quality)
- **Embeddings**: Cohere embed-multilingual-v3.0
- **Reranking**: Cohere rerank-multilingual-v3.0

## Cost Optimization

- Query rewriting: ~$0.001 per query
- URL validation: ~$0.001-0.003 per query (1-3 validations)
- Answer generation: ~$0.01 per query
- Embeddings: ~$0.0001 per query
- Reranking: ~$0.001 per query

**Total estimated cost: ~$0.01-0.02 per query**

## Performance

- Average query time: 5-10 seconds
- BM25 index: Built once, cached in memory
- Weaviate: Fast vector search (<1s)
- Bottleneck: LLM API calls (query rewriting, validation, generation)

## Future Enhancements

### Phase 1 (Current)
- ✅ RAG pipeline with URL validation
- ✅ Single URL output as clickable link
- ✅ Fallback for no relevant info

### Phase 2 (Future)
- [ ] Auto-redirect to validated URL
- [ ] Streaming responses
- [ ] Caching for common queries
- [ ] Multi-turn conversation support
- [ ] User feedback collection

## Troubleshooting

### Issue: "No relevant URLs found" for valid queries

**Solution:**
- Check if ingestion completed successfully
- Verify Weaviate has content: Check collection in Weaviate console
- Lower confidence threshold in `validate_urls_node` (currently 7.0)

### Issue: Slow response times

**Solution:**
- Reduce number of query rewrites (currently 2-3)
- Reduce search limits (currently 15-20 results)
- Use faster models for validation (already using Haiku)

### Issue: Wrong URLs returned

**Solution:**
- Increase confidence threshold (currently 7.0)
- Improve validation prompt in `validate_url_relevance`
- Check reranking is working correctly

## Comparison: Old vs New Agent

### Old Agent (react_agent.py)
- Basic LangGraph ReAct agent
- Tools: weather, stock price, web scraping
- No RAG capabilities
- No KKUC-specific knowledge

### New Agent (rag_agent.py)
- Custom LangGraph with RAG pipeline
- Advanced retrieval: hybrid search + reranking
- URL validation for quality control
- KKUC-specific knowledge from vector DB
- Empathetic, Danish responses
- Source attribution

## Integration with Frontend

The RAG agent is exposed via FastAPI and can be integrated with your frontend:

```typescript
// Example frontend integration
async function queryRAG(userQuery: string) {
  const response = await fetch('http://localhost:8000/rag/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: userQuery })
  });
  
  const result = await response.json();
  
  // Display answer
  console.log(result.answer);
  
  // Display source link (or redirect in future)
  if (result.source_url) {
    console.log(`Source: ${result.source_url}`);
  }
}
```

## Maintenance

### Updating Content
When KKUC website content changes:
1. Run ingestion pipeline: `poetry run python -m app.ingestion.run`
2. BM25 index will rebuild automatically on next query
3. No code changes needed

### Monitoring
- Log all queries and responses
- Track validation success rate
- Monitor API costs
- Collect user feedback on answer quality

## Support

For issues or questions:
1. Check this documentation
2. Review test_rag.py for examples
3. Check server logs for errors
4. Verify all environment variables are set
