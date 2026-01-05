# Scientific Research Agent

Multi-agent scientific research assistant built on Google ADK with Vertex AI Agent Engine.

**Model**: `gemini-2.5-flash` (all agents)

> **Note**: Preview models (e.g., `gemini-3-flash-preview`, `gemini-2.5-flash-preview`) may not be available in `us-central1`.
> Use GA model names without `-preview` suffix. See [Vertex AI Locations](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/locations).

## Architecture

Hierarchical multi-agent system using LLM-driven delegation:

```
Research Coordinator (agents/coordinator.py)
    ├── Ideation Agent     → Generate research hypotheses
    ├── Analysis Agent     → Statistical testing & analysis
    ├── Visualization Agent → Interactive Plotly charts
    └── Writer Agent       → Professional HTML reports
```

**Key principle**: Coordinator routes based on intent, never executes tools directly.

## Project Structure

```
scientific-research-agent/
├── main.py              # Entry point (AdkApp wrapper)
├── deploy.py            # Vertex AI Agent Engine deployment
├── test_agent.py        # Local async testing suite
├── requirements.txt     # Dependencies
├── agents/
│   ├── coordinator.py   # Parent orchestration agent
│   ├── ideation.py      # Hypothesis generation
│   ├── analysis.py      # Statistical analysis
│   ├── visualization.py # Chart creation
│   └── writer.py        # Report drafting
├── tools/
│   ├── bigquery.py      # SQL execution & schema (TCGA data)
│   ├── plotly_charts.py # Interactive HTML charts
│   ├── drive.py         # Google Drive integration
│   ├── docs.py          # Google Docs creation
│   ├── sheets.py        # Google Sheets + charts
│   └── gcs.py           # Cloud Storage utilities
└── output/              # Generated HTML files
```

## Data Source

Uses **TCGA (The Cancer Genome Atlas)** public data via BigQuery:
- 11,000+ cancer patients, 33 cancer types
- Tables: clinical, biospecimen, RNA expression, somatic mutations, copy number
- No data import needed - already accessible in `isb-cgc-bq.TCGA.*`

## Deployment

**Target**: Vertex AI Agent Engine

```bash
python3 deploy.py
```

**Requirements**:
- Staging bucket: `gs://{PROJECT_ID}-agent-staging`
- Data bucket: `{PROJECT_ID}-agent-data`
- BigQuery dataset: `research_agent_data`

### Critical: Keep Dependencies in Sync

The `deploy.py` requirements list MUST match `requirements.txt`. Missing dependencies cause the Reasoning Engine to fail on startup with import errors.

Key dependencies that must be in both files:
- `plotly>=5.18.0` (used by tools/plotly_charts.py)
- `python-dotenv` (used by main.py)

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Agent Engine fails to start | Missing dependency in deploy.py | Sync deploy.py requirements with requirements.txt |
| Import errors on deployment | Package not in deployment config | Add to deploy.py requirements list |
| Model 404 NOT_FOUND | Preview model not enabled | Enable model access in Vertex AI Model Garden |
| BigQuery 403 error | Missing permissions | Grant BigQuery Data Viewer role |

## Testing

```bash
python3 test_agent.py
```

Runs 5 test scenarios: ideation, analysis, visualization, writing, full pipeline.
