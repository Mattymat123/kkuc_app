# LangSmith Setup Guide

## Overview
LangSmith is now configured for your KKUC Assistant application. This will enable detailed tracing and inspection of your LangServe/LangGraph flows.

## Setup Steps

### 1. Install Dependencies
First, install the langsmith package:

```bash
cd KKUCAssistant/backend
poetry install
```

### 2. Get Your LangSmith API Key

1. Go to [https://smith.langchain.com](https://smith.langchain.com)
2. Sign up or log in with your account
3. Navigate to **Settings** (gear icon in the top right)
4. Go to **API Keys** section
5. Click **Create API Key**
6. Copy your API key

### 3. Update Your .env File

Replace `your-langsmith-api-key-here` in your `.env` file with your actual LangSmith API key:

```bash
LANGCHAIN_API_KEY=lsv2_pt_your_actual_api_key_here
```

### 4. Restart Your Application

After updating the `.env` file, restart your LangServe application:

```bash
cd KKUCAssistant/backend
poetry run python -m app.server
```

Or if using the start script:
```bash
cd KKUCAssistant
./scripts/start.sh
```

## What Gets Traced

With LangSmith enabled, you'll automatically see traces for:

- **Agent Execution Flow**: Complete flow through your LangGraph agent
- **RAG Workflow**: All steps in your RAG pipeline including:
  - Query processing
  - Vector search operations
  - Document retrieval
  - Response generation
- **LLM Calls**: Every call to Claude/OpenAI with:
  - Input prompts
  - Output responses
  - Token usage
  - Latency metrics
- **Tool Usage**: Any tools your agent uses
- **State Transitions**: How state changes through your graph

## Viewing Traces

1. Go to [https://smith.langchain.com](https://smith.langchain.com)
2. Navigate to your project: **kkuc-assistant**
3. You'll see all traces from your application
4. Click on any trace to see:
   - Complete execution timeline
   - Input/output for each step
   - Performance metrics
   - Error details (if any)

## Customizing the Project Name

You can change the project name by updating the `LANGCHAIN_PROJECT` variable in your `.env` file:

```bash
LANGCHAIN_PROJECT=my-custom-project-name
```

## Disabling Tracing

To temporarily disable tracing, set:

```bash
LANGCHAIN_TRACING_V2=false
```

## Troubleshooting

### Traces Not Appearing
- Verify your API key is correct
- Check that `LANGCHAIN_TRACING_V2=true` is set
- Ensure the application was restarted after updating `.env`
- Check for any error messages in the console

### API Key Issues
- Make sure you copied the full API key (starts with `lsv2_pt_`)
- Verify the key hasn't expired
- Check you have the correct permissions in LangSmith

## Monitoring & Cost Tracking

Once tracing is working, you can set up comprehensive monitoring:

📊 **See [LANGSMITH_MONITORING.md](./LANGSMITH_MONITORING.md) for detailed instructions on:**
- Setting up cost tracking dashboards
- Monitoring API expenses (OpenRouter, Cohere)
- Visualizing your RAG pipeline
- Setting up alerts for costs and performance
- Optimizing expenses

## Additional Resources

- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [LangSmith Tracing Guide](https://docs.smith.langchain.com/tracing)
- [LangGraph Tracing](https://langchain-ai.github.io/langgraph/how-tos/tracing/)
- [LangSmith Monitoring Guide](./LANGSMITH_MONITORING.md) ⭐
