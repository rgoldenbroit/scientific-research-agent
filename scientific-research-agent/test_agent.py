#!/usr/bin/env python3
"""
Local testing script for the Scientific Research Agent.
Run with: python3 test_agent.py
"""
import asyncio
from agent.main import app


async def test_ideation():
    """Test the ideation capability."""
    print("=" * 60)
    print("TESTING IDEATION CAPABILITY")
    print("=" * 60)
    
    async for event in app.async_stream_query(
        user_id="test-user",
        message="I'm studying the effects of microplastics on marine ecosystems. "
                "What novel hypotheses could I explore based on current research gaps?"
    ):
        if hasattr(event, 'content') and event.content:
            for part in event.content.get('parts', []):
                if 'text' in part:
                    print(part['text'])


async def test_analysis():
    """Test the analysis capability."""
    print("\n" + "=" * 60)
    print("TESTING ANALYSIS CAPABILITY")
    print("=" * 60)
    
    async for event in app.async_stream_query(
        user_id="test-user", 
        message="""I have experimental data showing:
        - Control group (n=50): Fish population declined 5% over 6 months
        - Treatment group (n=50): Fish population declined 30% in high microplastic areas
        - p-value from t-test: 0.003
        
        How should I interpret these results? What additional analyses would strengthen my conclusions?"""
    ):
        if hasattr(event, 'content') and event.content:
            for part in event.content.get('parts', []):
                if 'text' in part:
                    print(part['text'])


async def test_reporting():
    """Test the reporting capability."""
    print("\n" + "=" * 60)
    print("TESTING REPORTING CAPABILITY")
    print("=" * 60)
    
    async for event in app.async_stream_query(
        user_id="test-user",
        message="I need to write an NSF grant proposal to continue this microplastics research. "
                "Can you help me structure the proposal and identify key points to emphasize?"
    ):
        if hasattr(event, 'content') and event.content:
            for part in event.content.get('parts', []):
                if 'text' in part:
                    print(part['text'])


async def main():
    """Run all tests."""
    print("\n🧪 Scientific Research Agent - Local Testing\n")
    
    await test_ideation()
    await test_analysis()
    await test_reporting()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
