"""
BigQuery tools for data querying and schema inspection.
"""
import os
from google.cloud import bigquery

# BigQuery configuration - set via environment variables
BQ_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
BQ_DATASET = os.environ.get("AGENT_BQ_DATASET", "research_agent_data")


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
        bigquery.SchemaField("group_name", "STRING"),
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
        table_name: Name of the table. Can be:
            - Simple name (e.g., "my_table") - uses default project/dataset
            - Fully-qualified (e.g., "isb-cgc-bq.TCGA.clinical_gdc_current")

    Returns:
        dict containing table schema and metadata
    """
    try:
        client = _get_bigquery_client()

        # If table_name contains 2+ dots, treat as fully-qualified
        if table_name.count(".") >= 2:
            table_id = table_name
        else:
            if not BQ_PROJECT:
                return {"status": "error", "message": "No BigQuery project configured"}
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
        return {
            "status": "error",
            "message": "BigQuery project not configured. The GOOGLE_CLOUD_PROJECT environment variable is not set. Please ensure the .env file is loaded or set the environment variable."
        }

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
        error_msg = str(e)
        # Provide more context for common errors
        if "403" in error_msg or "Access Denied" in error_msg:
            error_msg = f"BigQuery access denied: {error_msg}. Check that the service account has BigQuery permissions."
        elif "404" in error_msg or "Not found" in error_msg:
            error_msg = f"Table or dataset not found: {error_msg}. Verify the table path is correct (project.dataset.table)."
        elif "400" in error_msg:
            error_msg = f"Invalid SQL query: {error_msg}. Check SQL syntax and column names."
        return {"status": "error", "message": error_msg}


def get_bigquery_schema(dataset_path: str = None) -> dict:
    """
    Get schema information for TCGA or other public BigQuery datasets.
    Useful for understanding what data is available before forming hypotheses.

    Args:
        dataset_path: Full dataset path (e.g., 'isb-cgc-bq.TCGA') or None to list
                      available TCGA datasets. Can also be a full table path like
                      'isb-cgc-bq.TCGA.clinical' to get specific table schema.

    Returns:
        dict containing dataset/table schema information
    """
    # Common TCGA tables for reference
    TCGA_TABLES = {
        "isb-cgc-bq.TCGA.clinical_gdc_current": "Clinical data: demographics, diagnosis, treatment, survival",
        "isb-cgc-bq.TCGA.biospecimen_gdc_current": "Biospecimen data: sample types, portions, analytes",
        "isb-cgc-bq.TCGA_hg38_data_v0.RNAseq_Gene_Expression": "Gene expression (RNA-seq) data",
        "isb-cgc-bq.TCGA_hg38_data_v0.Somatic_Mutation": "Somatic mutation data",
        "isb-cgc-bq.TCGA_hg38_data_v0.Copy_Number_Segment_Masked": "Copy number variation data",
    }

    if not dataset_path:
        # Return list of available TCGA datasets
        return {
            "status": "success",
            "message": "Available TCGA tables in BigQuery (isb-cgc-bq project)",
            "tables": TCGA_TABLES,
            "usage": "Call get_bigquery_schema with a specific table path to see its schema"
        }

    try:
        # Use configured project for authentication, even when querying public datasets
        client = _get_bigquery_client()

        # Check if it's a table path (has 3 parts) or dataset path (has 2 parts)
        parts = dataset_path.split(".")

        if len(parts) == 3:
            # It's a table - get table schema
            table = client.get_table(dataset_path)
            schema_info = []
            for field in table.schema:
                schema_info.append({
                    "name": field.name,
                    "type": field.field_type,
                    "mode": field.mode,
                    "description": field.description or ""
                })

            return {
                "status": "success",
                "table_id": dataset_path,
                "num_rows": table.num_rows,
                "num_columns": len(schema_info),
                "schema": schema_info,
                "description": table.description or "No description available"
            }

        elif len(parts) == 2:
            # It's a dataset - list tables
            tables = list(client.list_tables(dataset_path))
            table_list = []
            for t in tables[:50]:  # Limit to 50 tables
                table_list.append({
                    "table_id": t.table_id,
                    "full_path": f"{dataset_path}.{t.table_id}"
                })

            return {
                "status": "success",
                "dataset": dataset_path,
                "table_count": len(table_list),
                "tables": table_list,
                "note": "Call with full table path (project.dataset.table) to see schema"
            }

        else:
            return {
                "status": "error",
                "message": f"Invalid path format: {dataset_path}. Use 'project.dataset' or 'project.dataset.table'"
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}
