# LangGraph Studio Setup Guide

## 🎯 Overview
This guide will help you visualize your KKUC Agent flow using LangGraph Studio.

## 📋 Prerequisites
- LangGraph Studio installed (you mentioned you already downloaded it)
- Python 3.11 or compatible version
- All dependencies from `requirements.txt` installed

## 🚀 Quick Start

### Automatic Startup (Recommended)
LangGraph Studio now starts automatically when you run your application:

```bash
cd /Users/bruger/Documents/KKUC/KKUCAssistant
./scripts/start.sh
```

This will start:
1. Backend server (http://localhost:8000)
2. Frontend server (http://localhost:3000)
3. **LangGraph Studio with Cloudflare Tunnel** ← Your agent visualization

**Important**: When using the `--tunnel` flag (required for Brave browser), you must access LangGraph Studio through the **LangSmith Studio URL** provided in the console output, NOT `http://localhost:8123`.

Look for this in your terminal output:
```
- 🎨 Studio UI: https://eu.smith.langchain.com/studio/?baseUrl=https://XXXX.trycloudflare.com
```

Copy and paste that full URL into your browser (Brave will work with this URL).

### Manual Startup (Alternative)
If you prefer to start LangGraph Studio manually:

```bash
cd /Users/bruger/Documents/KKUC/KKUCAssistant
langgraph dev --tunnel
```

**Note**: The `--tunnel` flag is required when using Brave browser with Shields enabled, as Brave blocks localhost access via HTTP protocol by default. The tunnel creates a secure connection that bypasses this restriction.

Or open the LangGraph Studio desktop application and select the KKUCAssistant folder.

### What You'll See
Once LangGraph Studio is running, use the Studio UI URL from the console output (see above) to access:
- **Main Agent Graph**: Shows routing between Calendar and RAG workflows
- **Nodes**:
  - `route` - Entry point for intent classification
  - `calendar` - Calendar booking subgraph
  - `rag` - RAG search workflow
  
## 🗺️ Your Agent Architecture

```
┌─────────────────────────────────────────┐
│           KKUC Agent Main Graph         │
├─────────────────────────────────────────┤
│                                         │
│  START → route (classifier)             │
│           ↓         ↓                   │
│      calendar     rag                   │
│           ↓         ↓                   │
│         END       END                   │
│                                         │
└─────────────────────────────────────────┘

Calendar Subgraph (when calendar selected):
┌─────────────────────────────────────────┐
│  fetch_slots → select_slot →            │
│  confirm_booking → book_appointment     │
└─────────────────────────────────────────┘
```

## 🔍 What You'll See in Studio

### Main Graph Features
- **Conditional routing**: Based on booking keywords or LLM classification
- **Booking lock mechanism**: `booking_active` flag prevents routing changes
- **State management**: Tracks messages, booking context, and active status

### Interactive Features in Studio
1. **Step through execution**: See each node activate in real-time
2. **View state**: Inspect `AgentState` at each step
3. **Test different inputs**: Try booking vs. general queries
4. **Debug flows**: See why certain paths are taken

## 🧪 Testing Your Agent in Studio

### Test Case 1: Booking Flow
Input: "Jeg vil gerne booke en tid"
- Watch it route to `calendar` node
- See `booking_active` flag set to `True`

### Test Case 2: RAG Query
Input: "Hvad er KKUC's åbningstider?"
- Watch it route to `rag` node
- See RAG workflow execute

### Test Case 3: Booking Lock
1. Start booking: "book en tid"
2. While `booking_active=True`, send another message
3. Notice it stays locked in calendar workflow

## ⚙️ Configuration Details

Your `langgraph.json` configuration:
```json
{
  "graphs": {
    "agent": "./backend/app/agent.py:agent_executor"
  },
  "env": "./backend/.env",
  "python_version": "3.11"
}
```

This tells Studio:
- **Graph location**: `backend/app/agent.py` file, variable `agent_executor`
- **Environment**: Load variables from `backend/.env`
- **Python version**: Use Python 3.11

### Installation
The `langgraph-cli` package is included in your `requirements.txt` and will be installed automatically when you run `start.sh` for the first time.

If you need to install it manually:
```bash
pip install langgraph-cli
```

## 🐛 Troubleshooting

### Brave Browser Blocking Localhost
If you see an error about Brave blocking access to localhost:
- **Solution 1 (Recommended)**: The `start.sh` script automatically uses the `--tunnel` flag
- **Solution 2**: Disable Brave Shields for localhost
- **Solution 3**: Use a different browser (Chrome, Firefox, Safari)

The tunnel flag creates a secure connection that works with Brave's security settings.

### Studio can't find the graph
- Ensure you're opening the `KKUCAssistant` folder, not the parent `KKUC` folder
- Check that `agent_executor` exists in `backend/app/agent.py`

### Import errors
Make sure all dependencies are installed:
```bash
cd /Users/bruger/Documents/KKUC/KKUCAssistant
pip install -r requirements.txt
```

### Environment variables missing
- Verify `backend/.env` exists and contains required API keys
- Check Studio console for specific missing variables

### Can't see subgraphs
The calendar subgraph is embedded in the calendar node. To see its internal structure:
1. The main graph shows `calendar` as a single node
2. You can inspect the CalendarSubgraph code in `backend/app/workflows/calendar_subgraph.py`
3. Studio may show subgraph details in node properties

## 📚 Additional Resources

### Key Files
- **Main Agent**: `backend/app/agent.py` - Top-level routing logic
- **Calendar Subgraph**: `backend/app/workflows/calendar_subgraph.py` - Booking workflow
- **RAG Workflow**: `backend/app/workflows/simplified_rag_workflow.py` - Search logic
- **Calendar Tools**: `backend/app/tools/calendar_tools.py` - Google Calendar integration

### Documentation
- See `docs/CALENDAR_SUBGRAPH_ARCHITECTURE.md` for detailed calendar flow
- See `docs/STATE_MANAGEMENT_REFACTOR.md` for state design decisions

## 💡 Tips for Using Studio

1. **Use the replay feature**: Step backward through execution to understand decisions
2. **Inspect state**: Click on edges to see state transformations
3. **Edit and test**: Modify the graph code and reload to see changes
4. **Export diagrams**: Use Studio's export feature to save visualizations

## 🎨 Visual Customization

Your agent has clear checkpoint logging. In the Studio console you'll see:
- 📍 Checkpoint markers
- ✅ Completed steps
- → Next step indicators
- 🔒/🔓 Lock status changes

## 📝 Next Steps

1. Run `./scripts/start.sh` to start all services including LangGraph Studio
2. Open http://localhost:8123 in your browser
3. Explore the main agent graph visualization
4. Try running test inputs to see the flow in real-time
5. Inspect state at different checkpoints
6. Examine the calendar subgraph implementation
7. Modify routing logic and see visual updates

## 🔄 Integrated Workflow

Your development workflow is now streamlined:

1. **Start everything**: `./scripts/start.sh`
   - Backend API starts
   - Frontend UI starts
   - LangGraph Studio starts automatically
   - LangSmith monitoring is enabled (you mentioned it's already set up)

2. **Access your tools**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - **LangGraph Studio: Use the Studio UI URL from console output** (e.g., https://eu.smith.langchain.com/studio/?baseUrl=https://XXXX.trycloudflare.com)
   - LangSmith: https://smith.langchain.com

   **Note**: The Cloudflare tunnel URL changes each time you restart, so always check the console output for the current URL.

3. **Stop everything**: Press `Ctrl+C` in the terminal

Your agent is now ready to visualize in LangGraph Studio! 🎉
