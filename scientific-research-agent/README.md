# Scientific Research Agent for Gemini Enterprise

An AI agent that helps researchers with ideation, data analysis, and reporting.

## Workflow

```
HOME PC (Develop) → Git Repo → WORK PC (Deploy) → Gemini Enterprise
```

## Quick Start

### On Home Computer (Development)

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd scientific-research-agent

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip3 install -r requirements.txt

# 4. Test locally
python3 test_agent.py

# 5. Push changes
git add . && git commit -m "Your changes" && git push
```

### On Work Computer (Deployment)

```bash
# 1. Clone/pull latest
git clone <your-repo-url>  # or: git pull origin main
cd scientific-research-agent

# 2. Setup environment
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt

# 3. Authenticate to GCP
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud auth application-default login

# 4. Deploy (update PROJECT_ID in deploy.py first)
python3 deploy.py
```

## Project Structure

```
scientific-research-agent/
├── agent/
│   ├── __init__.py
│   ├── main.py      # Agent definition and instructions
│   └── tools.py     # Three core tools (ideation, analysis, reporting)
├── deploy.py        # Deployment script for Vertex AI
├── test_agent.py    # Local testing script
├── requirements.txt
└── README.md
```

## Capabilities

1. **Ideation**: Generate novel hypotheses and experiment ideas
2. **Analysis**: Analyze experimental data and extract insights  
3. **Reporting**: Help write reports, visualizations, and grant proposals

## Registration in Gemini Enterprise

After deployment, register the agent:

1. Go to **Cloud Console** → **Gemini Enterprise**
2. Select your app → **Agents** → **Add Agents**
3. Choose **"Custom agent via Agent Engine"**
4. Paste the Resource Name from deployment output
5. Save and share with your team

## Customization

- Edit `agent/main.py` to modify the agent's instructions
- Edit `agent/tools.py` to add new capabilities
- Change the model in `main.py` (e.g., `gemini-2.5-pro` for complex reasoning)
