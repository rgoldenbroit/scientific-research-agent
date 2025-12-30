#!/usr/bin/env python3
"""
Deploy the Scientific Research Agent to Vertex AI Agent Engine.

*** RUN THIS FROM YOUR WORK COMPUTER ***

Before running:
1. Replace YOUR_WORK_PROJECT_ID with your actual GCP project ID
2. Ensure you've run: gcloud auth application-default login
3. Ensure the staging bucket exists (see comments below)

Usage: python3 deploy.py
"""
import vertexai
from agent.main import app

# =============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# =============================================================================
PROJECT_ID = "YOUR_WORK_PROJECT_ID"      # Replace with your work GCP project ID
LOCATION = "us-central1"                  # Or your preferred region
STAGING_BUCKET = f"gs://{PROJECT_ID}-agent-staging"

# =============================================================================
# DEPLOYMENT
# =============================================================================

def main():
    print(f"🚀 Deploying Scientific Research Agent")
    print(f"   Project: {PROJECT_ID}")
    print(f"   Location: {LOCATION}")
    print(f"   Staging Bucket: {STAGING_BUCKET}")
    print()
    
    # Initialize Vertex AI client
    client = vertexai.Client(
        project=PROJECT_ID,
        location=LOCATION,
    )
    
    # Deploy the agent
    print("📦 Creating agent in Agent Engine (this may take a few minutes)...")
    
    remote_agent = client.agent_engines.create(
        agent=app,
        config={
            "requirements": [
                "google-cloud-aiplatform[agent_engines,adk]>=1.112",
                "google-adk"
            ],
            "staging_bucket": STAGING_BUCKET,
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
    print("   1. Go to Google Cloud Console → Gemini Enterprise")
    print("   2. Select your app → Agents → Add Agents")
    print("   3. Choose 'Custom agent via Agent Engine'")
    print("   4. Paste this Reasoning Engine path:")
    print()
    print(f"      {resource_name}")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
