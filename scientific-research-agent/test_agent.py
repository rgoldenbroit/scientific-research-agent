#!/usr/bin/env python3
"""
Local testing script for the Multi-Agent Scientific Research Assistant.
Run with: python3 test_agent.py
"""
import asyncio
from main import app


async def test_ideation():
    """Test the ideation capability via coordinator -> ideation_agent."""
    print("=" * 70)
    print("TEST 1: IDEATION (Coordinator -> Ideation Agent)")
    print("=" * 70)

    async for event in app.async_stream_query(
        user_id="test-user",
        message="What interesting research questions could I explore with TCGA breast cancer data? "
                "I'm particularly interested in survival outcomes and genetic markers."
    ):
        if hasattr(event, 'content') and event.content:
            for part in event.content.get('parts', []):
                if 'text' in part:
                    print(part['text'])


async def test_analysis():
    """Test the analysis capability via coordinator -> analysis_agent."""
    print("\n" + "=" * 70)
    print("TEST 2: ANALYSIS (Coordinator -> Analysis Agent)")
    print("=" * 70)

    async for event in app.async_stream_query(
        user_id="test-user",
        message="Test if TP53 mutations are associated with survival in TCGA breast cancer patients. "
                "Run a survival analysis comparing TP53 mutant vs wild-type."
    ):
        if hasattr(event, 'content') and event.content:
            for part in event.content.get('parts', []):
                if 'text' in part:
                    print(part['text'])


async def test_visualization():
    """Test the visualization capability via coordinator -> visualization_agent."""
    print("\n" + "=" * 70)
    print("TEST 3: VISUALIZATION (Coordinator -> Visualization Agent)")
    print("=" * 70)

    async for event in app.async_stream_query(
        user_id="test-user",
        message="Create a Kaplan-Meier survival curve comparing TP53 mutant vs wild-type "
                "breast cancer patients. Save it to Google Drive."
    ):
        if hasattr(event, 'content') and event.content:
            for part in event.content.get('parts', []):
                if 'text' in part:
                    print(part['text'])


async def test_writing():
    """Test the writing capability via coordinator -> writer_agent."""
    print("\n" + "=" * 70)
    print("TEST 4: WRITING (Coordinator -> Writer Agent)")
    print("=" * 70)

    async for event in app.async_stream_query(
        user_id="test-user",
        message="Write up a Results section for my analysis of TP53 mutations and survival "
                "in breast cancer. Create it as a Google Doc."
    ):
        if hasattr(event, 'content') and event.content:
            for part in event.content.get('parts', []):
                if 'text' in part:
                    print(part['text'])


async def test_multi_agent_workflow():
    """Test a full multi-agent workflow: ideation -> analysis -> viz -> writing."""
    print("\n" + "=" * 70)
    print("TEST 5: FULL WORKFLOW (Multiple Agents)")
    print("=" * 70)

    async for event in app.async_stream_query(
        user_id="test-user",
        message="I want to investigate the relationship between PIK3CA mutations and "
                "survival in breast cancer. First generate hypotheses, then analyze, "
                "create a visualization, and write up the results."
    ):
        if hasattr(event, 'content') and event.content:
            for part in event.content.get('parts', []):
                if 'text' in part:
                    print(part['text'])


async def main():
    """Run all tests."""
    print("\n🧬 Multi-Agent Scientific Research Assistant - Local Testing\n")
    print("This tests the coordinator's ability to route to specialized agents.\n")

    # Run individual capability tests
    await test_ideation()
    await test_analysis()
    await test_visualization()
    await test_writing()

    # Run full workflow test
    await test_multi_agent_workflow()

    print("\n" + "=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
