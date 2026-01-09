#!/usr/bin/env python3
"""
Update an existing deployed agent on Vertex AI Agent Engine.

This is FASTER than deploy.py because it updates in-place instead of creating new.

Usage: python3 update.py <RESOURCE_NAME>

Example:
    python3 update.py projects/second-impact-444322-p8/locations/us-central1/reasoningEngines/1234567890
"""
import sys
import vertexai
from main import app

# =============================================================================
# CONFIGURATION - Same as deploy.py
# =============================================================================
PROJECT_ID = "second-impact-444322-p8"
LOCATION = "us-central1"
STAGING_BUCKET = f"gs://{PROJECT_ID}-agent-staging"
DATA_BUCKET = f"{PROJECT_ID}-agent-data"
BQ_DATASET = "research_agent_data"

# =============================================================================
# UPDATE
# =============================================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 update.py <RESOURCE_NAME>")
        print()
        print("To find your resource name, run:")
        print("  gcloud ai reasoning-engines list --project={} --region={}".format(PROJECT_ID, LOCATION))
        print()
        print("Or check the output from your last deploy.py run.")
        sys.exit(1)

    resource_name = sys.argv[1]

    print(f"🔄 Updating Agent Engine deployment")
    print(f"   Resource: {resource_name}")
    print(f"   Project: {PROJECT_ID}")
    print(f"   Location: {LOCATION}")
    print()

    # Initialize Vertex AI client
    client = vertexai.Client(
        project=PROJECT_ID,
        location=LOCATION,
    )

    # Update the agent (faster than create)
    print("📦 Updating agent (this is faster than full deployment)...")

    updated_agent = client.agent_engines.update(
        name=resource_name,
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
                "python-dotenv",
                "pyyaml>=6.0"
            ],
            "extra_packages": ["./agents", "./tools", "./config"],
            "staging_bucket": STAGING_BUCKET,
            "env_vars": {
                "PROJECT_ID": PROJECT_ID,
                "AGENT_DATA_BUCKET": DATA_BUCKET,
                "AGENT_BQ_DATASET": BQ_DATASET,
                "ENABLE_DRIVE_UPLOAD": "true",
                "GMAIL_IMPERSONATE_EMAIL": "admin@rgoldenbroit.altostrat.com",
            }
        }
    )

    print()
    print("=" * 70)
    print("✅ UPDATE SUCCESSFUL!")
    print("=" * 70)
    print()
    print(f"Resource: {resource_name}")
    print()
    print("Your agent has been updated. Changes are live immediately.")
    print("=" * 70)


if __name__ == "__main__":
    main()
