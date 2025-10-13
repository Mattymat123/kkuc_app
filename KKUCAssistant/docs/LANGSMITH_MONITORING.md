# LangSmith Monitoring & Cost Tracking Guide

## Overview
This guide explains how to monitor your KKUC Assistant's performance, track costs, and visualize your pipeline in LangSmith.

## What Gets Automatically Tracked

With LangSmith enabled, the following is automatically tracked for every request:

### 1. **Pipeline Visualization**
Your RAG workflow is automatically traced with these steps:
- **Query Rewriting** - Multiple query variations generated
- **Hybrid Search** - Vector + keyword search across Weaviate
- **Reranking** - Cohere reranking of results
- **URL Validation** - LLM-based relevance checking
- **Answer Generation** - Final response creation

### 2. **Cost Tracking**
LangSmith automatically tracks costs for:
- **OpenRouter API calls** (Claude Sonnet 4.5)
  - Query rewriting
  - URL validation
  - Answer generation
- **Cohere API calls**
  - Reranking operations
- **Token usage** for each LLM call

### 3. **Performance Metrics**
- **Latency** for each step
- **Total request time**
- **Success/failure rates**
- **Error tracking**

## Viewing Your Traces

### Access Your Project
1. Go to https://smith.langchain.com
2. Navigate to **Projects** → **kkuc-assistant**
3. You'll see all traces from your application

### Understanding the Trace View
Each trace shows:
```
Main Agent (process_query)
  └─ RAG Workflow
      ├─ Query Rewriting (LLM call)
      ├─ Hybrid Search (Weaviate)
      ├─ Reranking (Cohere)
      ├─ URL Validation (LLM call)
      └─ Answer Generation (LLM call)
```

Click on any step to see:
- Input/output data
- Token counts
- Cost per call
- Execution time
- Error details (if any)

## Setting Up Cost Monitoring

### 1. Create a Dashboard

1. In LangSmith, go to **Monitoring** → **Dashboards**
2. Click **New Dashboard**
3. Name it "KKUC Cost & Performance"

### 2. Add Cost Tracking Widgets

Add these widgets to track expenses:

#### **Total Cost Over Time**
- Widget type: **Line Chart**
- Metric: `Total Cost`
- Group by: `Day`
- Filter: Project = `kkuc-assistant`

#### **Cost by Model**
- Widget type: **Bar Chart**
- Metric: `Cost`
- Group by: `Model Name`
- Shows breakdown: Claude vs Cohere costs

#### **Token Usage**
- Widget type: **Line Chart**
- Metrics: `Input Tokens`, `Output Tokens`
- Group by: `Hour`

#### **Requests per Day**
- Widget type: **Line Chart**
- Metric: `Request Count`
- Group by: `Day`

### 3. Add Performance Widgets

#### **Average Latency**
- Widget type: **Line Chart**
- Metric: `Latency (ms)`
- Group by: `Hour`

#### **Success Rate**
- Widget type: **Gauge**
- Metric: `Success Rate (%)`
- Shows percentage of successful requests

#### **Error Rate**
- Widget type: **Line Chart**
- Metric: `Error Count`
- Group by: `Hour`

## Setting Up Alerts

### Cost Alerts

1. Go to **Monitoring** → **Alerts**
2. Click **New Alert**
3. Configure:

#### **Daily Cost Threshold**
```
Alert Name: Daily Cost Exceeds Budget
Condition: Total Cost > $10 (adjust as needed)
Time Window: 24 hours
Project: kkuc-assistant
Notification: Email
```

#### **Hourly Request Spike**
```
Alert Name: Unusual Request Volume
Condition: Request Count > 100
Time Window: 1 hour
Project: kkuc-assistant
Notification: Email
```

### Performance Alerts

#### **High Latency**
```
Alert Name: Slow Response Time
Condition: Average Latency > 5000ms
Time Window: 15 minutes
Project: kkuc-assistant
Notification: Email
```

#### **Error Rate**
```
Alert Name: High Error Rate
Condition: Error Rate > 5%
Time Window: 1 hour
Project: kkuc-assistant
Notification: Email
```

## Cost Breakdown by Component

Your KKUC Assistant uses these services:

### **OpenRouter (Claude Sonnet 4.5)**
- **Query Rewriting**: ~500 tokens per request
- **URL Validation**: ~1000 tokens per URL checked (up to 3 URLs)
- **Answer Generation**: ~2000 tokens per response
- **Estimated cost**: ~$0.01-0.03 per user query

### **Cohere Reranking**
- **Reranking**: 15 documents per query
- **Estimated cost**: ~$0.001 per query

### **Weaviate**
- **Vector Search**: Free (self-hosted or cloud free tier)
- **Keyword Search**: Free

### **Total Estimated Cost per Query**: $0.011-0.031

## Monitoring Best Practices

### 1. **Daily Review**
- Check dashboard each morning
- Review cost trends
- Identify any anomalies

### 2. **Weekly Analysis**
- Analyze most expensive queries
- Review error patterns
- Optimize slow operations

### 3. **Monthly Reporting**
- Total costs by service
- Usage patterns
- Performance improvements

## Optimizing Costs

### Reduce Token Usage
1. **Limit context length** in answer generation (currently 6000 chars)
2. **Reduce reranking candidates** (currently 15, could reduce to 10)
3. **Cache common queries** (implement caching layer)

### Optimize Pipeline
1. **Skip URL validation** for high-confidence results (confidence > 9)
2. **Reduce query rewrites** from 3 to 2 variations
3. **Implement response caching** for identical queries

## Viewing Specific Metrics

### Cost per User Query
```
Filter: run_type = "chain"
Metric: cost
Group by: trace_id
```

### Most Expensive Operations
```
Sort by: cost (descending)
View: Individual runs
```

### Token Usage by Step
```
Filter: Project = kkuc-assistant
Metric: token_usage
Group by: run_name
```

## Exporting Data

### Export Traces for Analysis
1. Go to **Projects** → **kkuc-assistant**
2. Click **Export**
3. Choose format: CSV or JSON
4. Select date range
5. Download for offline analysis

### API Access
Use LangSmith SDK to programmatically access metrics:

```python
from langsmith import Client

client = Client()

# Get runs for analysis
runs = client.list_runs(
    project_name="kkuc-assistant",
    start_time="2025-01-01",
    end_time="2025-01-31"
)

# Calculate total cost
total_cost = sum(run.total_cost for run in runs if run.total_cost)
print(f"Total cost: ${total_cost:.2f}")
```

## Troubleshooting

### Traces Not Appearing
- Verify `LANGCHAIN_ENDPOINT=https://eu.api.smith.langchain.com` is set
- Check API key is valid
- Ensure application was restarted after `.env` changes

### Missing Cost Data
- Cost tracking requires model pricing data
- OpenRouter costs are tracked automatically
- Cohere costs may need manual configuration

### Incomplete Traces
- Check for errors in application logs
- Verify all LLM calls are using LangChain wrappers
- Ensure proper error handling in code

## Additional Resources

- [LangSmith Dashboards Documentation](https://docs.langchain.com/langsmith/dashboards)
- [LangSmith Alerts Documentation](https://docs.langchain.com/langsmith/alerts)
- [Cost Tracking Guide](https://docs.langchain.com/langsmith/cost-tracking)
- [Trace Query Syntax](https://docs.langchain.com/langsmith/trace-query-syntax)

## Summary

With LangSmith properly configured, you now have:
- ✅ Automatic tracing of your entire RAG pipeline
- ✅ Real-time cost tracking for all API calls
- ✅ Performance monitoring and alerts
- ✅ Detailed visualization of each request
- ✅ Historical data for optimization

Your traces will appear at: https://smith.langchain.com/projects/kkuc-assistant
