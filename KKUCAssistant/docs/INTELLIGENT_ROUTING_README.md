# Intelligent Routing & Conversation Context

## Overview

The KKUC chatbot now features intelligent routing that decides whether to use RAG search or answer directly from conversation context. This significantly improves response times and user experience for follow-up questions.

## Key Improvements

### 1. **Intelligent Routing System**
- Uses a lightweight LLM (GPT-4o-mini) to decide if RAG search is needed
- Routes to direct answer when question can be answered from conversation history
- Routes to RAG search when new information is required

### 2. **Conversation Context Awareness**
- Maintains conversation history across messages
- Resolves pronouns and references (e.g., "his number" → "Nicolai Halberg's number")
- Provides quick, contextual answers without unnecessary database searches

### 3. **Performance Benefits**
- **Direct answers**: ~1-2 seconds (no RAG search)
- **RAG answers**: ~5-7 seconds (full search pipeline)
- Reduces unnecessary API calls and database queries

## Architecture

```
User Query
    ↓
Route Query Node (GPT-4o-mini)
    ↓
Decision: RAG or DIRECT?
    ↓
    ├─→ DIRECT: Answer from Context Node (Claude Sonnet 4.5)
    │   - Uses conversation history
    │   - Fast response (1-2s)
    │   - No database search
    │
    └─→ RAG: RAG Search Node
        - Full RAG pipeline
        - Database search + reranking
        - Slower but comprehensive (5-7s)
```

## Example Conversation Flow

### Test Results

```
User: "Hvem er jeres direktør?"
→ Routing: RAG search (new information needed)
→ Response: Full answer with link, phone, email (6.59s)

User: "Hvad er hans nummer?"
→ Routing: Direct answer (context available)
→ Response: "📞 Nicolai Halbergs telefonnummer er 2565 4545" (1-2s)

User: "Og hans email?"
→ Routing: Direct answer (context available)
→ Response: "📧 Nicolai Halbergs email er nih@kkuc.dk" (1-2s)

User: "Hvad er åbningstiderne?"
→ Routing: RAG search (new information needed)
→ Response: Searches database for opening hours (5.20s)
```

## Routing Logic

The routing system analyzes:

1. **Conversation History**: Last 3 exchanges (6 messages)
2. **Question Type**: 
   - Follow-up with pronouns → DIRECT
   - New topic → RAG
   - Clarification → DIRECT if context is clear
3. **Context Availability**: Can the question be answered from history?

### Routing Examples

| Question | Previous Context | Decision | Reason |
|----------|-----------------|----------|---------|
| "hvad er hans nummer?" | Just discussed person | DIRECT | Pronoun reference clear |
| "hvem er direktøren?" | No context | RAG | New information needed |
| "fortæl mere om det" | Clear topic | DIRECT | Context available |
| "hvad er åbningstiderne?" | Any context | RAG | Specific new info needed |

## Implementation Details

### Agent State
```python
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add]
    needs_rag: bool  # Routing decision
```

### Key Components

1. **route_query_node**: Decides RAG vs DIRECT
2. **answer_from_context_node**: Generates answer from conversation history
3. **rag_search_node**: Performs full RAG pipeline

### Models Used

- **Routing**: GPT-4o-mini (fast, cost-effective)
- **Direct Answers**: Claude Sonnet 4.5 (high quality)
- **RAG Answers**: Claude Sonnet 4.5 (high quality)

## Benefits

### User Experience
✅ Faster responses for follow-up questions
✅ Natural conversation flow
✅ Accurate pronoun resolution
✅ Consistent context awareness

### Performance
✅ 60-70% reduction in response time for follow-ups
✅ Fewer unnecessary database queries
✅ Lower API costs for simple questions

### Accuracy
✅ Better understanding of conversation context
✅ Proper handling of references and pronouns
✅ Maintains conversation coherence

## Testing

Run the test suite:
```bash
cd KKUCAssistant/backend
python3 test_conversation_context.py
```

The test verifies:
- Initial RAG search for new questions
- Direct answers for follow-ups
- Proper context resolution
- Routing decision accuracy

## Future Enhancements

Potential improvements:
- [ ] Cache recent RAG results for faster re-queries
- [ ] Multi-turn conversation summarization
- [ ] User preference learning
- [ ] Context window optimization
- [ ] A/B testing of routing strategies

## Configuration

The routing behavior can be tuned by adjusting:
- Number of messages in context window (currently 6)
- Routing prompt examples
- Temperature settings for routing LLM
- Confidence thresholds

## Monitoring

Key metrics to track:
- Routing decision accuracy
- Response time by route type
- User satisfaction with follow-up answers
- RAG vs DIRECT ratio
