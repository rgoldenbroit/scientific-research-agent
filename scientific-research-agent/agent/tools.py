"""
Tools for the Scientific Research Agent.
Each tool represents a core capability.
"""
import random


def generate_synthetic_data(
    data_type: str,
    num_samples: int = 50,
    num_groups: int = 2,
    include_noise: bool = True
) -> dict:
    """
    Generate realistic synthetic scientific data for demonstrations and testing.

    Args:
        data_type: Type of data - 'proteomics', 'genomics', 'clinical_trial',
                   'environmental', or 'behavioral'
        num_samples: Number of samples per group (default: 50)
        num_groups: Number of experimental groups (default: 2, e.g., control vs treatment)
        include_noise: Whether to add realistic noise/variation (default: True)

    Returns:
        dict containing synthetic dataset with metadata and the data itself
    """
    # Define realistic parameters for each data type
    data_configs = {
        "proteomics": {
            "features": ["Protein_A", "Protein_B", "Protein_C", "Protein_D", "Protein_E",
                        "IL6", "TNF_alpha", "CRP", "Albumin", "Hemoglobin"],
            "units": "ng/mL",
            "base_range": (10, 1000),
            "group_labels": ["Control", "Disease"] if num_groups == 2 else [f"Group_{i+1}" for i in range(num_groups)]
        },
        "genomics": {
            "features": ["BRCA1", "TP53", "EGFR", "KRAS", "MYC",
                        "PTEN", "APC", "RB1", "CDKN2A", "PIK3CA"],
            "units": "TPM",
            "base_range": (0.1, 500),
            "group_labels": ["Wild_Type", "Mutant"] if num_groups == 2 else [f"Group_{i+1}" for i in range(num_groups)]
        },
        "clinical_trial": {
            "features": ["Blood_Pressure_Systolic", "Blood_Pressure_Diastolic", "Heart_Rate",
                        "BMI", "Cholesterol_Total", "Cholesterol_LDL", "Cholesterol_HDL",
                        "Glucose_Fasting", "HbA1c", "Creatinine"],
            "units": "mixed",
            "base_range": (50, 200),
            "group_labels": ["Placebo", "Treatment"] if num_groups == 2 else [f"Arm_{i+1}" for i in range(num_groups)]
        },
        "environmental": {
            "features": ["Temperature_C", "pH", "Dissolved_O2", "Salinity",
                        "Nitrate", "Phosphate", "Chlorophyll_a", "Turbidity"],
            "units": "mixed",
            "base_range": (0, 50),
            "group_labels": ["Site_Control", "Site_Impact"] if num_groups == 2 else [f"Site_{i+1}" for i in range(num_groups)]
        },
        "behavioral": {
            "features": ["Response_Time_ms", "Accuracy_Pct", "Error_Rate",
                        "Trials_Completed", "Learning_Rate", "Fatigue_Index"],
            "units": "mixed",
            "base_range": (100, 1000),
            "group_labels": ["Control", "Experimental"] if num_groups == 2 else [f"Condition_{i+1}" for i in range(num_groups)]
        }
    }

    config = data_configs.get(data_type, data_configs["proteomics"])

    # Generate the synthetic data
    data_rows = []
    for group_idx, group_label in enumerate(config["group_labels"][:num_groups]):
        for sample_num in range(num_samples):
            row = {
                "sample_id": f"{group_label}_{sample_num + 1:03d}",
                "group": group_label
            }

            for feature in config["features"]:
                base_val = random.uniform(*config["base_range"])
                # Add group effect (20-40% difference for some features)
                if group_idx > 0 and random.random() > 0.5:
                    base_val *= random.uniform(1.2, 1.6)
                # Add noise if requested
                if include_noise:
                    noise = random.gauss(0, base_val * 0.15)
                    base_val = max(0.01, base_val + noise)
                row[feature] = round(base_val, 3)

            data_rows.append(row)

    return {
        "status": "data_generated",
        "data_type": data_type,
        "num_samples_per_group": num_samples,
        "num_groups": num_groups,
        "total_samples": num_samples * num_groups,
        "features": config["features"],
        "groups": config["group_labels"][:num_groups],
        "units": config["units"],
        "noise_included": include_noise,
        "data": data_rows,
        "csv_format": "sample_id,group," + ",".join(config["features"])
    }

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
