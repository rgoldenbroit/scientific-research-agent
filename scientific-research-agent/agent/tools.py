"""
Tools for the Scientific Research Agent.
Each tool represents one of the three core capabilities.
"""

def generate_hypotheses(
    research_topic: str,
    background_context: str,
    num_hypotheses: int = 3
) -> dict:
    """
    Generate novel research hypotheses based on the provided topic and context.
    
    Args:
        research_topic: The main area of scientific inquiry
        background_context: Existing research, observations, or preliminary data
        num_hypotheses: Number of hypotheses to generate (default: 3)
    
    Returns:
        dict containing generated hypotheses with rationale and suggested experiments
    """
    return {
        "status": "ready_for_ideation",
        "topic": research_topic,
        "context_provided": bool(background_context),
        "requested_count": num_hypotheses
    }


def analyze_experimental_data(
    data_description: str,
    data_format: str,
    analysis_type: str = "exploratory"
) -> dict:
    """
    Analyze experimental results to extract meaningful insights.
    
    Args:
        data_description: Description of the experimental data and its structure
        data_format: Format of the data (e.g., 'tabular', 'time_series', 'categorical')
        analysis_type: Type of analysis - 'exploratory', 'statistical', or 'comparative'
    
    Returns:
        dict containing analysis framework and key questions to address
    """
    return {
        "status": "ready_for_analysis",
        "data_format": data_format,
        "analysis_type": analysis_type,
        "framework": "statistical" if analysis_type == "statistical" else "descriptive"
    }


def prepare_research_report(
    report_type: str,
    target_audience: str,
    sections_needed: list[str] = None
) -> dict:
    """
    Help prepare research documentation including reports, visualizations, or grant proposals.
    
    Args:
        report_type: Type of document - 'summary', 'full_report', 'grant_proposal', or 'presentation'
        target_audience: Who will read this - 'scientific_peers', 'funding_agency', 'general_public'
        sections_needed: Specific sections to include (optional)
    
    Returns:
        dict containing report template and guidance
    """
    templates = {
        "grant_proposal": ["Abstract", "Specific Aims", "Background", "Methodology", 
                          "Preliminary Data", "Timeline", "Budget Justification"],
        "full_report": ["Abstract", "Introduction", "Methods", "Results", 
                        "Discussion", "Conclusions", "References"],
        "summary": ["Key Findings", "Implications", "Next Steps"],
        "presentation": ["Title", "Background", "Methods", "Results", "Conclusions"]
    }
    
    return {
        "status": "ready_for_reporting",
        "report_type": report_type,
        "audience": target_audience,
        "suggested_sections": sections_needed or templates.get(report_type, templates["summary"])
    }
