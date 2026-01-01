# Research Assistant Multi-Agent Architecture

## Context

I'm building a multi-agent research assistant for Google Cloud's Gemini Enterprise using the Agent Development Kit (ADK). This will be demoed to university customers (Harvard, NYU, Columbia, Cornell) who do scientific research.

## Current State

I have an existing ADK project with a single research agent that has three capabilities (ideation, analysis, reporting). I need to refactor this into a multi-agent architecture where specialized sub-agents handle each capability.

## Target Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    🎯 RESEARCH COORDINATOR                      │
│                                                                 │
│  Role: Understand intent, plan steps, delegate to sub-agents    │
│  Tools: None (only calls sub-agents)                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
     ┌──────────────────────┼──────────────────────┐
     ▼                      ▼                      ▼
┌──────────┐          ┌──────────┐          ┌──────────┐
│    💡    │          │    📊    │          │    📈    │
│ IDEATION │ ──────▶  │ ANALYSIS │ ──────▶  │   VIZ    │
│  AGENT   │          │  AGENT   │          │  AGENT   │
└────┬─────┘          └────┬─────┘          └────┬─────┘
     │                     │                     │
     ▼                     ▼                     ▼
 [tools]               [tools]               [tools]
                                                 │
                                                 ▼
                                           ┌──────────┐
                                           │    📝    │
                                           │  WRITER  │
                                           │  AGENT   │
                                           └────┬─────┘
                                                │
                                                ▼
                                            [tools]
```

## Key Design Principle: Tools vs Sub-Agents

- **Tools** = Functions that execute without reasoning (BigQuery queries, save to Drive, etc.)
- **Sub-Agents** = LLMs that can reason and decide HOW to accomplish something

Sub-agents handle the *thinking*, tools handle the *doing*.

## Agent Specifications

### 1. Research Coordinator (Parent Agent)

| Attribute | Value |
|-----------|-------|
| Role | Route requests, orchestrate workflow, synthesize final output |
| Model | gemini-2.0-flash |
| Tools | Sub-agents only (ideation_agent, analysis_agent, viz_agent, writer_agent) |
| Key behavior | Determines which sub-agents to call and in what order based on user request |

**Why no direct tools?** Keeps it focused on coordination. If it had tools, it might try to "do" instead of "delegate."

### 2. Ideation Agent (Sub-Agent)

| Attribute | Value |
|-----------|-------|
| Role | Generate research questions, hypotheses, experiment ideas |
| When called | "What should I investigate?" / "What might explain this?" / Starting a new research project |
| Tools | `web_search` (literature), `bigquery_schema_tool` (inspect available data) |
| Output | Ranked list of testable hypotheses with rationale |

**Key behavior:** Should check what data is actually available before proposing hypotheses.

### 3. Analysis Agent (Sub-Agent)

| Attribute | Value |
|-----------|-------|
| Role | Statistical analysis, pattern detection, hypothesis testing |
| When called | "Analyze my data" / "Test this hypothesis" / "Is this significant?" |
| Tools | `bigquery_tool`, `code_execution` (for scipy/statsmodels) |
| Output | Statistical results, p-values, findings summary as structured data |

### 4. Visualization Agent (Sub-Agent)

| Attribute | Value |
|-----------|-------|
| Role | Create charts, figures, plots |
| When called | After analysis when findings need visual representation |
| Tools | `code_execution` (matplotlib/seaborn), `drive_save_tool` |
| Output | PNG files saved to Google Drive (returns Drive URLs) |

**Important:** Output goes to Drive, NOT rendered in chat UI (avoids known rendering issues in Gemini Enterprise).

### 5. Writer Agent (Sub-Agent)

| Attribute | Value |
|-----------|-------|
| Role | Draft reports, grant sections, papers |
| When called | "Write up these findings" / "Draft my Results section" |
| Tools | `google_docs_create`, `drive_embed_image` |
| Output | Formatted Google Doc with embedded visualizations (returns Doc URL) |

## Data Source: TCGA in BigQuery

Using public cancer genomics data that's already in BigQuery (no data import needed):

| Table | Location | Contents |
|-------|----------|----------|
| Clinical | `isb-cgc-bq.TCGA.clinical` | 11,000+ patients, demographics, survival, treatment response |
| Gene Expression | `isb-cgc-bq.TCGA.RNAseq_Gene_Expression` | Expression levels, 10,000+ samples |
| Somatic Mutations | `isb-cgc-bq.TCGA.Somatic_Mutation` | All mutations across 33 cancer types |
| Protein Expression | `isb-cgc-bq.TCGA.Protein_Expression` | Protein abundance data |

## Example Demo Flow

**User prompt:** "I have access to TCGA breast cancer data. What interesting questions could I investigate?"

| Step | Agent | Action |
|------|-------|--------|
| 1 | Coordinator | Recognizes ideation request, routes to Ideation Agent |
| 2 | Ideation Agent | Searches literature, inspects TCGA schema, proposes 3 hypotheses |
| 3 | User | Selects: "Test if TP53+PIK3CA co-mutation predicts worse survival" |
| 4 | Coordinator | Routes to Analysis Agent |
| 5 | Analysis Agent | Queries clinical + mutation tables, runs survival analysis |
| 6 | Coordinator | Passes results to Viz Agent |
| 7 | Viz Agent | Creates Kaplan-Meier survival curves, saves to Drive |
| 8 | Coordinator | Passes findings + chart URLs to Writer Agent |
| 9 | Writer Agent | Drafts Results section in NIH format, embeds charts |
| 10 | Coordinator | Returns Google Doc link to user |

## Sample Ideation Agent Output

```
Based on current literature gaps and TCGA-BRCA data availability, here are testable hypotheses:

**Hypothesis 1:** Triple-negative breast cancer patients with high tumor mutation 
burden show distinct immune gene signatures.
- Rationale: TMB is emerging as immunotherapy biomarker, understudied in TNBC
- Data needed: Mutation counts + expression data (both available)

**Hypothesis 2:** Co-occurrence of TP53 and PIK3CA mutations predicts worse 
survival than either mutation alone.
- Rationale: Two most common BRCA mutations, interaction effects unclear
- Data needed: Mutation + clinical/survival (both available)

**Hypothesis 3:** Young-onset breast cancer (<40) has distinct molecular 
signatures independent of subtype.
- Rationale: Age-specific patterns could inform personalized treatment
- Data needed: Clinical (age) + expression (both available)

Which hypothesis would you like to investigate?
```

## Sample BigQuery Queries for Analysis Agent

**Get surviving breast cancer patients:**
```sql
SELECT case_barcode
FROM `isb-cgc-bq.TCGA.clinical`
WHERE project_short_name = 'TCGA-BRCA'
  AND vital_status = 'Alive'
  AND days_to_last_followup > 1825
```

**Count mutations per gene:**
```sql
SELECT 
  Hugo_Symbol AS gene,
  COUNT(*) AS mutation_count,
  COUNT(DISTINCT case_barcode) AS patients_affected
FROM `isb-cgc-bq.TCGA.Somatic_Mutation`
WHERE case_barcode IN (/* survivors from previous query */)
GROUP BY gene
ORDER BY mutation_count DESC
LIMIT 20
```

## Project Structure Target

```
research-assistant/
├── agents/
│   ├── coordinator.py      # Parent agent - orchestration only
│   ├── ideation.py         # Hypothesis generation
│   ├── analysis.py         # Statistical analysis
│   ├── visualization.py    # Chart creation
│   └── writer.py           # Report drafting
├── tools/
│   ├── bigquery.py         # Query execution
│   ├── drive.py            # File save/retrieval
│   ├── docs.py             # Google Docs creation
│   └── search.py           # Web/literature search
├── main.py                 # Entry point
└── requirements.txt
```

## Key Implementation Notes

1. **Sub-agents as tools:** In ADK, register sub-agents as tools that the coordinator can call
2. **Context passing:** Each sub-agent receives relevant context from coordinator (not full conversation)
3. **Output to Drive/Docs:** Final artifacts go to Google Drive/Docs, not chat UI (avoids rendering issues)
4. **Ideation first:** Research flow should start with hypothesis generation, not queries

## Request

Please help me refactor my existing single-agent research assistant into this multi-agent architecture. Start by examining my current code structure, then implement the coordinator and sub-agents with proper tool registration.
