"""
Tools for the Scientific Research Agent.
Each tool represents a core capability.
"""
import json
import os
import random
import uuid
from datetime import datetime

from google.cloud import storage
from google.cloud import bigquery

# GCS bucket for storing generated data - set via environment variable
DATA_BUCKET = os.environ.get("AGENT_DATA_BUCKET", "")

# BigQuery configuration - set via environment variables
BQ_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
BQ_DATASET = os.environ.get("AGENT_BQ_DATASET", "research_agent_data")


def _get_storage_client():
    """Get a GCS storage client."""
    return storage.Client()


def _get_bigquery_client():
    """Get a BigQuery client."""
    return bigquery.Client(project=BQ_PROJECT)


def _ensure_bq_dataset():
    """Ensure the BigQuery dataset exists, create if not."""
    if not BQ_PROJECT:
        return False

    client = _get_bigquery_client()
    dataset_id = f"{BQ_PROJECT}.{BQ_DATASET}"

    try:
        client.get_dataset(dataset_id)
    except Exception:
        # Dataset doesn't exist, create it
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"
        client.create_dataset(dataset, exists_ok=True)

    return True


def _upload_to_bigquery(data_rows: list, table_name: str, features: list, groups: list, data_type: str) -> str:
    """
    Upload data to BigQuery and return the table reference.

    Args:
        data_rows: List of data dictionaries
        table_name: Name for the BigQuery table
        features: List of feature column names
        groups: List of group names
        data_type: Type of data (for metadata)

    Returns:
        BigQuery table reference string (project.dataset.table)
    """
    if not BQ_PROJECT:
        return ""

    if not _ensure_bq_dataset():
        return ""

    client = _get_bigquery_client()
    table_id = f"{BQ_PROJECT}.{BQ_DATASET}.{table_name}"

    # Define schema based on the data
    schema = [
        bigquery.SchemaField("sample_id", "STRING"),
        bigquery.SchemaField("group_name", "STRING"),  # renamed from 'group' which is reserved
    ]
    for feature in features:
        schema.append(bigquery.SchemaField(feature, "FLOAT64"))

    # Create or replace table
    table = bigquery.Table(table_id, schema=schema)
    table = client.create_table(table, exists_ok=True)

    # Prepare rows for insertion (rename 'group' to 'group_name')
    rows_to_insert = []
    for row in data_rows:
        new_row = {
            "sample_id": row["sample_id"],
            "group_name": row["group"]
        }
        for feature in features:
            new_row[feature] = row.get(feature)
        rows_to_insert.append(new_row)

    # Insert data
    errors = client.insert_rows_json(table_id, rows_to_insert)
    if errors:
        raise Exception(f"BigQuery insert errors: {errors}")

    return table_id


def _upload_to_gcs(data: dict, filename: str) -> str:
    """Upload data to GCS and return the gs:// URI."""
    if not DATA_BUCKET:
        return ""

    client = _get_storage_client()
    bucket = client.bucket(DATA_BUCKET)
    blob = bucket.blob(f"datasets/{filename}")

    blob.upload_from_string(
        json.dumps(data, indent=2),
        content_type="application/json"
    )

    return f"gs://{DATA_BUCKET}/datasets/{filename}"


def _download_from_gcs(gcs_path: str) -> dict:
    """Download and parse JSON data from GCS."""
    # Parse gs:// URI
    if not gcs_path.startswith("gs://"):
        raise ValueError(f"Invalid GCS path: {gcs_path}")

    path_parts = gcs_path[5:].split("/", 1)
    bucket_name = path_parts[0]
    blob_path = path_parts[1] if len(path_parts) > 1 else ""

    client = _get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    content = blob.download_as_text()
    return json.loads(content)


def list_datasets(bucket_name: str = None) -> dict:
    """
    List available datasets in the GCS bucket.

    Args:
        bucket_name: Optional bucket name override. Uses default if not provided.

    Returns:
        dict containing list of available datasets with metadata
    """
    bucket = bucket_name or DATA_BUCKET
    if not bucket:
        return {
            "status": "error",
            "message": "No data bucket configured. Set AGENT_DATA_BUCKET environment variable."
        }

    client = _get_storage_client()
    gcs_bucket = client.bucket(bucket)
    blobs = gcs_bucket.list_blobs(prefix="datasets/")

    datasets = []
    for blob in blobs:
        if blob.name.endswith(".json"):
            datasets.append({
                "name": blob.name.split("/")[-1],
                "path": f"gs://{bucket}/{blob.name}",
                "size_bytes": blob.size,
                "created": blob.time_created.isoformat() if blob.time_created else None
            })

    return {
        "status": "success",
        "bucket": bucket,
        "dataset_count": len(datasets),
        "datasets": datasets
    }


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

    # Create result with metadata
    result = {
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

    # Generate unique table/file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]

    # Save to BigQuery if project is configured
    if BQ_PROJECT:
        table_name = f"{data_type}_{timestamp}_{unique_id}"
        try:
            bq_table = _upload_to_bigquery(
                data_rows=data_rows,
                table_name=table_name,
                features=config["features"],
                groups=config["group_labels"][:num_groups],
                data_type=data_type
            )
            result["bigquery_table"] = bq_table
            result["bigquery_status"] = "saved_to_bigquery"
        except Exception as e:
            result["bigquery_table"] = None
            result["bigquery_status"] = f"error: {str(e)}"
    else:
        result["bigquery_table"] = None
        result["bigquery_status"] = "not_saved_no_project_configured"

    # Also save to GCS if bucket is configured (for backward compatibility)
    if DATA_BUCKET:
        filename = f"{data_type}_{timestamp}_{unique_id}.json"
        gcs_path = _upload_to_gcs(result, filename)
        result["gcs_path"] = gcs_path
        result["storage_status"] = "saved_to_gcs"
    else:
        result["gcs_path"] = None
        result["storage_status"] = "not_saved_no_bucket_configured"

    return result

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
    analysis_type: str = "exploratory",
    gcs_path: str = None
) -> dict:
    """
    Analyze experimental results to extract meaningful insights.

    Args:
        data_description: Description of the experimental data and its structure
        data_format: Format of the data (e.g., 'tabular', 'time_series', 'categorical')
        analysis_type: Type of analysis - 'exploratory', 'statistical', or 'comparative'
        gcs_path: Optional GCS path (gs://...) to load data from

    Returns:
        dict containing analysis framework, loaded data (if gcs_path provided), and guidance
    """
    result = {
        "status": "ready_for_analysis",
        "data_format": data_format,
        "analysis_type": analysis_type,
        "framework": "statistical" if analysis_type == "statistical" else "descriptive"
    }

    # Load data from GCS if path provided
    if gcs_path:
        try:
            loaded_data = _download_from_gcs(gcs_path)
            result["data_loaded"] = True
            result["gcs_path"] = gcs_path
            result["data_type"] = loaded_data.get("data_type", "unknown")
            result["features"] = loaded_data.get("features", [])
            result["groups"] = loaded_data.get("groups", [])
            result["total_samples"] = loaded_data.get("total_samples", 0)
            result["data"] = loaded_data.get("data", [])

            # Calculate basic statistics for each feature by group
            if result["data"] and result["features"]:
                stats_by_group = {}
                for group in result["groups"]:
                    group_data = [row for row in result["data"] if row.get("group") == group]
                    group_stats = {}
                    for feature in result["features"]:
                        values = [row[feature] for row in group_data if feature in row]
                        if values:
                            group_stats[feature] = {
                                "mean": round(sum(values) / len(values), 3),
                                "min": round(min(values), 3),
                                "max": round(max(values), 3),
                                "n": len(values)
                            }
                    stats_by_group[group] = group_stats
                result["statistics_by_group"] = stats_by_group

        except Exception as e:
            result["data_loaded"] = False
            result["error"] = str(e)
    else:
        result["data_loaded"] = False
        result["note"] = "No GCS path provided. Provide gcs_path to load and analyze stored data."

    return result


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


def list_table_ids() -> dict:
    """
    List all BigQuery tables in the research_agent_data dataset.

    Returns:
        dict containing list of table IDs
    """
    if not BQ_PROJECT:
        return {"status": "error", "message": "No BigQuery project configured"}

    try:
        client = _get_bigquery_client()
        dataset_ref = f"{BQ_PROJECT}.{BQ_DATASET}"
        tables = list(client.list_tables(dataset_ref))

        table_list = [table.table_id for table in tables]
        return {
            "status": "success",
            "dataset": dataset_ref,
            "table_count": len(table_list),
            "tables": table_list
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_table_info(table_name: str) -> dict:
    """
    Get schema and row count for a BigQuery table.

    Args:
        table_name: Name of the table (without project/dataset prefix)

    Returns:
        dict containing table schema and metadata
    """
    if not BQ_PROJECT:
        return {"status": "error", "message": "No BigQuery project configured"}

    try:
        client = _get_bigquery_client()
        table_id = f"{BQ_PROJECT}.{BQ_DATASET}.{table_name}"
        table = client.get_table(table_id)

        schema_info = [{"name": field.name, "type": field.field_type} for field in table.schema]

        return {
            "status": "success",
            "table_id": table_id,
            "num_rows": table.num_rows,
            "num_columns": len(schema_info),
            "schema": schema_info,
            "created": table.created.isoformat() if table.created else None
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def execute_sql(sql_query: str) -> dict:
    """
    Execute a SQL query against BigQuery and return results.

    Args:
        sql_query: The SQL query to execute. Use fully qualified table names
                   (project.dataset.table) or reference tables in research_agent_data dataset.

    Returns:
        dict containing query results as a list of rows
    """
    if not BQ_PROJECT:
        return {"status": "error", "message": "No BigQuery project configured"}

    try:
        client = _get_bigquery_client()
        query_job = client.query(sql_query)
        results = query_job.result()

        rows = []
        for row in results:
            rows.append(dict(row))

        return {
            "status": "success",
            "row_count": len(rows),
            "rows": rows[:100],  # Limit to 100 rows
            "truncated": len(rows) > 100
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
