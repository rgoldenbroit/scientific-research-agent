#!/usr/bin/env python3
"""
Deploy the Multi-Agent Scientific Research Assistant to Vertex AI Agent Engine.

*** RUN THIS FROM YOUR WORK COMPUTER ***

Before running:
1. Replace YOUR_WORK_PROJECT_ID with your actual GCP project ID
2. Ensure you've run: gcloud auth application-default login
3. Ensure the staging bucket exists (see comments below)
4. Enable Drive API: gcloud services enable drive.googleapis.com

Usage: python3 deploy.py
"""
import vertexai
from main import app

# =============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# =============================================================================
PROJECT_ID = "second-impact-444322-p8"   # GCP project ID
LOCATION = "us-central1"                  # Agent Engine requires us-central1
STAGING_BUCKET = f"gs://{PROJECT_ID}-agent-staging"
DATA_BUCKET = f"{PROJECT_ID}-agent-data"  # Bucket for storing generated datasets
BQ_DATASET = "research_agent_data"        # BigQuery dataset for storing data

# =============================================================================
# DEPLOYMENT
# =============================================================================

def main():
    print(f"🚀 Deploying Multi-Agent Scientific Research Assistant")
    print(f"   Project: {PROJECT_ID}")
    print(f"   Location: {LOCATION}")
    print(f"   Staging Bucket: {STAGING_BUCKET}")
    print(f"   Data Bucket: {DATA_BUCKET}")
    print(f"   BigQuery Dataset: {BQ_DATASET}")
    print()

    # Initialize Vertex AI client
    client = vertexai.Client(
        project=PROJECT_ID,
        location=LOCATION,
    )

    # Deploy the agent
    print("📦 Creating multi-agent system in Agent Engine (this may take a few minutes)...")

    remote_agent = client.agent_engines.create(
        agent=app,
        config={
            "requirements": [
                "google-cloud-aiplatform[agent_engines,adk]>=1.112",
                "google-adk>=1.1.0",
                "google-cloud-storage",
                "google-cloud-bigquery",
                "google-api-python-client",
                "google-auth-oauthlib",
                "scipy",
                "statsmodels",
                "matplotlib",
                "seaborn",
                "lifelines",
                "cloudpickle",
                "pydantic",
                "plotly>=5.18.0",
                "python-dotenv"
            ],
            "extra_packages": ["./agents", "./tools"],
            "staging_bucket": STAGING_BUCKET,
            "env_vars": {
                "AGENT_DATA_BUCKET": DATA_BUCKET,
                "AGENT_BQ_DATASET": BQ_DATASET,
                "ENABLE_DRIVE_UPLOAD": "true",  # Enable Google Drive uploads for shareable links
                "AGENT_DRIVE_FOLDER_ID": "1zVEOPAXaOyRAQe1OyA1Kcw4ZD_V6fssc",  # Shared Drive folder for charts/reports
            }
        }
    )
    
    # Extract resource information
    resource_name = remote_agent.api_resource.name
    resource_id = resource_name.split("/")[-1]
    
    print()
    print("=" * 70)
    print("✅ DEPLOYMENT SUCCESSFUL!")
    print("=" * 70)
    print()
    print(f"Full Resource Name: {resource_name}")
    print(f"Resource ID: {resource_id}")
    print()
    print("📋 NEXT STEPS:")
    print(f"   1. Create data bucket (if not exists):")
    print(f"      gsutil mb -l {LOCATION} gs://{DATA_BUCKET}")
    print()
    print(f"   2. Create BigQuery dataset (if not exists):")
    print(f"      bq mk --location={LOCATION} {PROJECT_ID}:{BQ_DATASET}")
    print()
    print("   3. Go to Google Cloud Console → Gemini Enterprise")
    print("   4. Select your app → Agents → Add Agents")
    print("   5. Choose 'Custom agent via Agent Engine'")
    print("   6. Paste this Reasoning Engine path:")
    print()
    print(f"      {resource_name}")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
