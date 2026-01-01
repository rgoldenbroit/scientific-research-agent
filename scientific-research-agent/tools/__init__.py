"""
Tools package for the Multi-Agent Scientific Research Assistant.
Each module provides specialized tool functions for different capabilities.
"""

from .bigquery import (
    execute_sql,
    list_table_ids,
    get_table_info,
    get_bigquery_schema,
)
from .gcs import (
    list_datasets,
    generate_synthetic_data,
    analyze_experimental_data,
)
from .drive import (
    save_to_drive,
    save_image_to_drive,
    get_drive_file_url,
    list_drive_files,
)
from .docs import (
    create_google_doc,
    append_to_doc,
    embed_image_in_doc,
    add_heading_to_doc,
)
from .sheets import (
    create_spreadsheet_with_chart,
    add_chart_to_spreadsheet,
    get_spreadsheet_url,
)

__all__ = [
    # BigQuery tools
    "execute_sql",
    "list_table_ids",
    "get_table_info",
    "get_bigquery_schema",
    # GCS tools
    "list_datasets",
    "generate_synthetic_data",
    "analyze_experimental_data",
    # Drive tools
    "save_to_drive",
    "save_image_to_drive",
    "get_drive_file_url",
    "list_drive_files",
    # Docs tools
    "create_google_doc",
    "append_to_doc",
    "embed_image_in_doc",
    "add_heading_to_doc",
    # Sheets tools
    "create_spreadsheet_with_chart",
    "add_chart_to_spreadsheet",
    "get_spreadsheet_url",
]
