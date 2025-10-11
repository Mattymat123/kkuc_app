# KKUC Assistant Architecture

## Overview
The KKUC Assistant is built with a clean, modular architecture that separates concerns into three main layers:

1. **Main Agent** - Orchestrates workflows and handles LangServe deployment
2. **Workflows** - Implements specific task patterns (e.g., RAG)
3. **Tools** - Provides specialized functionality for workflows

## Directory Structure

```
app/
├── agent.py                    # Main agent orchestrator
├── server.py                   # FastAPI server with LangServe
├── workflows/                  # Different workflow implementations
│   ├── __init__.py
│   └── rag_workflow.py        # RAG workflow implementation
└── tools/                      # Tools organized by workflow
    ├── web_scraping.py        # General web scraping tool
    └── rag/                   # RAG-specific tools
        ├── __init__.py        # SearchResult dataclass
        ├── search_tools.py    # Vector, BM25, hybrid search, reranking
        ├── query_tools.py     # Query rewriting
        └── validation_tools.py # URL relevance validation
```

## Components

### 1. Main Agent (`agent.py`)
- **Purpose**: Main orchestrator compatible with LangServe
- **Responsibilities**:
  - Manages conversation state
  - Routes queries to appropriate workflows
  - Formats responses for LangServe
- **Key Features**:
  - LangGraph-based state management
  - Compatible with LangServe deployment
  - Handles message history

### 2. Workflows (`workflows/`)
Each workflow implements a specific task pattern.

#### RAG Workflow (`rag_workflow.py`)
- **Purpose**: Retrieve and validate information from KKUC's knowledge base
- **Process**:
  1. Query rewriting (multiple variations)
  2. Hybrid search (vector + BM25)
  3. Reranking with Cohere
  4. Group results by URL
  5. Validate URL relevance
  6. Generate answer from validated content
- **Output**: Answer with source URL

### 3. Tools (`tools/`)
Tools are organized by the workflow they support.

#### RAG Tools (`tools/rag/`)

**Search Tools** (`search_tools.py`)
- Vector search using Weaviate + Cohere embeddings
- BM25 keyword search
- Hybrid search combining both methods
- Reranking with Cohere reranker

**Query Tools** (`query_tools.py`)
- Query rewriting for better retrieval
- Generates 2-3 alternative formulations

**Validation Tools** (`validation_tools.py`)
- URL relevance validation
- Confidence scoring (1-10)
- Ensures quality of retrieved information

## Data Flow

```
User Query
    ↓
Main Agent (agent.py)
    ↓
RAG Workflow (workflows/rag_workflow.py)
    ↓
┌─────────────────────────────────────┐
│ 1. Query Tools: Rewrite query       │
│ 2. Search Tools: Hybrid search      │
│ 3. Search Tools: Rerank results     │
│ 4. Validation Tools: Validate URLs  │
│ 5. Generate answer with LLM         │
└─────────────────────────────────────┘
    ↓
Main Agent formats response
    ↓
LangServe returns to client
```

## LangServe Deployment

The agent is deployed via LangServe at the `/agent` endpoint:

```python
# server.py
from .agent import agent_executor

kkuc_agent_runnable = agent_executor.with_types(input_type=ChatInputType)
add_routes(app, kkuc_agent_runnable, path="/agent")
```

### API Usage

**Endpoint**: `POST /agent/invoke`

**Request**:
```json
{
  "input": {
    "messages": [
      {
        "type": "human",
        "content": "Hvad er behandlingsmuligheder for alkoholmisbrug?"
      }
    ]
  }
}
```

**Response**:
```json
{
  "output": {
    "messages": [
      {
        "type": "human",
        "content": "Hvad er behandlingsmuligheder for alkoholmisbrug?"
      },
      {
        "type": "ai",
        "content": "KKUC tilbyder forskellige behandlingsmuligheder...\n\n📎 Kilde: https://kkuc.dk/behandling"
      }
    ]
  }
}
```

## Adding New Workflows

To add a new workflow:

1. Create workflow file in `workflows/`
2. Create corresponding tools in `tools/[workflow_name]/`
3. Import and initialize in `agent.py`
4. Add routing logic in agent's `process_query_node`

Example:
```python
# workflows/new_workflow.py
class NewWorkflow:
    def run(self, query: str) -> dict:
        # Implementation
        pass

# agent.py
from .workflows.new_workflow import NewWorkflow

class KKUCAgent:
    def __init__(self):
        self.new_workflow = NewWorkflow()
```

## Environment Variables

Required environment variables (see `.env`):
- `OPENROUTER_API_KEY` - For LLM access
- `WEAVIATE_URL` - Weaviate cloud URL
- `WEAVIATE_API_KEY` - Weaviate API key
- `COHERE_API_KEY` - For embeddings and reranking

## Testing

Run the server:
```bash
cd KKUCAssistant/backend
python3 -m app.server
```

Access API docs: `http://localhost:8000/docs`

## Benefits of This Architecture

1. **Separation of Concerns**: Each component has a single responsibility
2. **Modularity**: Easy to add new workflows and tools
3. **Testability**: Components can be tested independently
4. **Maintainability**: Clear structure makes code easy to understand
5. **Scalability**: New workflows don't affect existing ones
6. **LangServe Compatible**: Seamless deployment with LangServe
