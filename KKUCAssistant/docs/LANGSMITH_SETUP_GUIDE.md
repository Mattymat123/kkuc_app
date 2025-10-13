# LangSmith Setup Guide for KKUC Assistant

This guide explains how to set up LangSmith tracing for the simplified RAG workflow.

## What is LangSmith?

LangSmith is LangChain's platform for debugging, testing, and monitoring LLM applications. It provides:
- **Tracing**: Visualize every step of your agent's execution
- **Debugging**: See inputs, outputs, and latency for each component
- **Monitoring**: Track performance and errors in production

## Setup Instructions

### 1. Create a LangSmith Account

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Sign up for a free account
3. Create a new project (e.g., "KKUC-Assistant")

### 2. Get Your API Key

1. In LangSmith, go to Settings → API Keys
2. Create a new API key
3. Copy the key (you won't be able to see it again)

### 3. Configure Environment Variables

Add these variables to your `.env` file:

```bash
# LangSmith credentials (for tracing and monitoring)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your-langsmith-api-key-here
LANGCHAIN_PROJECT=KKUC-Assistant
```

**Important**: Replace `your-langsmith-api-key-here` with your actual API key.

### 4. Verify Setup

The simplified RAG workflow is already instrumented with `@traceable` decorators. Once you set the environment variables, tracing will automatically start.

## Viewing Traces in LangSmith

### What You'll See

The simplified workflow has 3 main traced steps:

1. **Step 1: Query Rewriting**
   - Shows original query and generated variations
   - Displays the query rewriting LLM call

2. **Step 2: Hybrid Search with Reranking**
   - Shows vector search results
   - Shows BM25 search results
   - Displays reranking process with Cohere

3. **Step 3: URL Validation and Answer Generation**
   - Shows URL grouping
   - Displays validation checks for each URL
   - Shows final answer generation with full context

### How to Access Traces

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Select your project (e.g., "KKUC-Assistant")
3. Click on "Traces" in the left sidebar
4. You'll see a list of all workflow executions

### Understanding the Trace View

Each trace shows:
- **Timeline**: Visual representation of execution flow
- **Inputs/Outputs**: What went into and came out of each step
- **Latency**: How long each step took
- **Metadata**: Additional context like model used, tokens, etc.

## Workflow Visualization

The LangGraph workflow will appear as a graph in LangSmith:

```
[User Query]
     ↓
[Step 1: Query Rewriting]
     ↓
[Step 2: Hybrid Search + Reranking]
     ↓
[Step 3: URL Validation + Answer Generation]
     ↓
[Final Answer]
```

Each node is clickable to see detailed information.

## Benefits of the Simplified Workflow

### Reduced Latency
- **Before**: 6+ steps with multiple LLM calls
- **After**: 3 clear steps with optimized LLM usage
- **Result**: Faster response times

### Reduced Code Complexity
- **Before**: Complex state management across many nodes
- **After**: Linear flow with clear state transitions
- **Result**: Easier to debug and maintain

### Better Tracing
- Each step is clearly labeled and traceable
- Easy to identify bottlenecks
- Clear visualization of the entire pipeline

## Troubleshooting

### Traces Not Appearing

1. **Check environment variables**: Ensure all LangSmith variables are set correctly
2. **Verify API key**: Make sure your API key is valid
3. **Check project name**: Ensure the project exists in LangSmith
4. **Restart server**: After adding environment variables, restart the backend server

### Slow Traces

If you notice slow execution:
1. Check the "Latency" column in LangSmith
2. Identify which step is taking the longest
3. Common bottlenecks:
   - Query rewriting (LLM call)
   - Reranking (Cohere API call)
   - Answer generation (LLM call with large context)

## Advanced Features

### Custom Metadata

You can add custom metadata to traces by modifying the `@traceable` decorator:

```python
@traceable(
    name="Step 1: Query Rewriting",
    metadata={"version": "1.0", "model": "claude-3.5-haiku"}
)
def step1_rewrite_query(self, state: RAGState) -> RAGState:
    # ...
```

### Filtering Traces

In LangSmith, you can filter traces by:
- Date range
- Status (success/error)
- Latency
- Custom metadata

### Comparing Runs

LangSmith allows you to compare multiple runs side-by-side to:
- Test different prompts
- Compare model performance
- Analyze A/B tests

## Next Steps

1. Set up your environment variables
2. Run a test query
3. View the trace in LangSmith
4. Explore the detailed execution flow
5. Use insights to optimize performance

For more information, visit the [LangSmith documentation](https://docs.smith.langchain.com).
