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

### Current Deployment

| Resource | Value |
|----------|-------|
| Project ID | `second-impact-444322-p8` |
| Region | `us-central1` |
| Resource Name | `projects/second-impact-444322-p8/locations/us-central1/reasoningEngines/8168769961515286528` |
| Resource ID | `8168769961515286528` |
| Staging Bucket | `gs://second-impact-444322-p8-agent-staging` |
| Data Bucket | `second-impact-444322-p8-agent-data` |
| Service Account | `research-agent@second-impact-444322-p8.iam.gserviceaccount.com` |

### Deploy Commands

```bash
# Fresh deployment (slow, creates new resource)
python3 deploy.py

# Update existing deployment (faster, in-place update)
python3 update.py projects/second-impact-444322-p8/locations/us-central1/reasoningEngines/8168769961515286528
```

### Requirements
- Staging bucket: `gs://{PROJECT_ID}-agent-staging`
- Data bucket: `{PROJECT_ID}-agent-data`
- BigQuery dataset: `research_agent_data`

### Google Drive Integration (Shareable Links)

Charts and reports are automatically uploaded to Google Drive and return shareable links that users can click directly in the chat.

**Setup**:
1. Enable Drive API in your GCP project
2. Grant the service account `drive.file` scope access
3. (Optional) Set `AGENT_DRIVE_FOLDER_ID` env var to store files in a specific folder

**Environment Variables**:
- `ENABLE_DRIVE_UPLOAD`: Set to `"false"` to disable (default: `"true"`)
- `AGENT_DRIVE_FOLDER_ID`: Optional folder ID to organize uploaded files

### Critical: Keep Dependencies in Sync

The `deploy.py` requirements list MUST match `requirements.txt`. Missing dependencies cause the Reasoning Engine to fail on startup with import errors.

Key dependencies that must be in both files:
- `plotly>=5.18.0` (used by tools/plotly_charts.py)
- `python-dotenv` (used by main.py)

### Gmail Integration (Domain-Wide Delegation)

Email sending requires Google Workspace domain-wide delegation.

**Environment Variables** (set in deploy.py):
- `GMAIL_IMPERSONATE_EMAIL`: User to impersonate (e.g., `admin@rgoldenbroit.altostrat.com`)
- `GMAIL_SA_KEY_SECRET`: Secret Manager path to SA key (e.g., `projects/second-impact-444322-p8/secrets/gmail-sa-key/versions/latest`)

**Setup Requirements**:
1. Service account key stored in Secret Manager
2. Domain-wide delegation enabled on service account in GCP
3. Scopes authorized in Google Workspace Admin (`admin.google.com` → Security → API Controls → Domain Wide Delegation)
4. Required scopes: `https://www.googleapis.com/auth/gmail.send,https://www.googleapis.com/auth/gmail.compose`
5. Impersonated user must have Gmail enabled in their Workspace account

**Demo Mode**: All emails are redirected to `DEMO_EMAIL_OVERRIDE` in `tools/email.py` (currently `admin@rgoldenbroit.altostrat.com`)

**Known Issue**: Demo account doesn't have Gmail enabled due to org policy - email sending will fail with "Mail service not enabled"

## Debugging

### View Agent Logs

```bash
# Gmail-specific logs
gcloud logging read 'textPayload=~"Gmail"' \
  --project=second-impact-444322-p8 \
  --freshness=30m \
  --limit=50

# All agent errors
gcloud logging read 'resource.type="aiplatform.googleapis.com/ReasoningEngine" severity>=ERROR' \
  --project=second-impact-444322-p8 \
  --limit=20

# Recent agent logs (all)
gcloud logging read 'resource.type="aiplatform.googleapis.com/ReasoningEngine"' \
  --project=second-impact-444322-p8 \
  --freshness=10m \
  --limit=100
```

### Log Interpretation

| Log Message | Meaning |
|-------------|---------|
| `[Gmail Auth] SUCCESS via Secret Manager` | Credentials loaded correctly |
| `[Gmail Auth] Secret Manager error: 403` | SA needs `secretmanager.secretAccessor` role on secret |
| `[Gmail Auth] ADC credentials don't support with_subject()` | Fallback to ADC failed, Secret Manager not configured |
| `[Gmail] API error (raw): Mail service not enabled` | Impersonated user doesn't have Gmail |
| `function response parts mismatch` | A tool returned None instead of dict - check `@safe_tool` decorator |

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Agent Engine fails to start | Missing dependency in deploy.py | Sync deploy.py requirements with requirements.txt |
| Import errors on deployment | Package not in deployment config | Add to deploy.py requirements list |
| Model 404 NOT_FOUND | Preview model not enabled | Enable model access in Vertex AI Model Garden |
| BigQuery 403 error | Missing permissions | Grant BigQuery Data Viewer role |
| Drive upload fails | Drive API not enabled or missing permissions | Enable Drive API, grant `drive.file` scope |
| No shareable link returned | `ENABLE_DRIVE_UPLOAD=false` or auth error | Check env var and service account permissions |
| Gmail "Precondition check failed" | Domain-wide delegation not working | Check Secret Manager permissions, Workspace Admin config |
| Gmail "Mail service not enabled" | Impersonated user lacks Gmail | Use a different user with Gmail enabled |
| Duplicate analysis output | LLM not following instructions | Strengthen "ONE OUTPUT ONLY" in agent instructions |
| Silent tool failures | Tool not returning dict | Ensure `@safe_tool` decorator on all tools |

## Testing

```bash
python3 test_agent.py
```

Runs 5 test scenarios: ideation, analysis, visualization, writing, full pipeline.

## Key Patterns

### Tool Safety

All tools MUST use the `@safe_tool` decorator to ensure they always return a dict:

```python
from tools.email import safe_tool  # or define locally

@safe_tool
def my_tool(arg: str) -> dict:
    # Tool implementation
    return {"status": "success", "data": result}
```

Without this, tool failures cause "function response parts mismatch" errors that break the entire agent.

### Logging for Cloud Visibility

Use Python's `logging` module instead of `print()` for Cloud Logging visibility:

```python
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logger.info("Message visible in Cloud Logging")  # ✓
print("This won't appear in Cloud Logging")       # ✗
```

### Agent Instructions

When agents produce duplicate or malformed output:
1. Add explicit "ONE OUTPUT ONLY" instruction at the TOP of the instruction string
2. Add consolidation rules requiring all queries complete before output
3. Check if tool errors are causing retries

## Files Quick Reference

| File | Purpose | When to Modify |
|------|---------|----------------|
| `deploy.py` | Fresh deployment config | Adding dependencies, env vars |
| `update.py` | In-place update config | Same as deploy.py (keep in sync) |
| `tools/email.py` | Gmail integration | Email auth issues |
| `agents/analysis.py` | Statistical analysis agent | Output formatting, query patterns |
| `agents/coordinator.py` | Main orchestrator | Adding/removing sub-agents |
| `requirements.txt` | Local dependencies | Adding packages (sync with deploy.py) |
