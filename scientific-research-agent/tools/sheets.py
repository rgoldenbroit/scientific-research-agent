"""
Google Sheets tools for data visualization.
Creates spreadsheets with embedded charts using the Sheets API.
"""
from typing import Optional

from google.auth import default
from googleapiclient.discovery import build

# Scopes required for Sheets access
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]


def _get_sheets_service():
    """Get an authenticated Google Sheets service."""
    try:
        credentials, project = default(scopes=SCOPES)
        return build("sheets", "v4", credentials=credentials)
    except Exception as e:
        return None


def _get_drive_service():
    """Get an authenticated Google Drive service for permissions."""
    try:
        credentials, project = default(scopes=SCOPES)
        return build("drive", "v3", credentials=credentials)
    except Exception as e:
        return None


def create_spreadsheet_with_chart(
    title: str,
    data: dict,
    chart_type: str = "COLUMN",
    chart_title: str = "",
    x_axis_title: str = "",
    y_axis_title: str = "",
) -> dict:
    """
    Create a Google Spreadsheet with data and an embedded chart.

    This is the main visualization function. It creates a spreadsheet,
    populates it with data, and adds a chart that visualizes the data.

    Args:
        title: Title for the spreadsheet (e.g., "Survival Analysis Results")
        data: Dictionary where keys are column headers and values are lists of data.
              Example: {"Age Group": ["<50", "50-70", ">70"], "Count": [45, 89, 67]}
        chart_type: Type of chart. Options:
            - "COLUMN" (vertical bars) - good for comparing categories
            - "BAR" (horizontal bars) - good for long category names
            - "LINE" - good for trends over time
            - "PIE" - good for proportions
            - "SCATTER" - good for correlations
            - "AREA" - good for cumulative data
        chart_title: Title displayed on the chart
        x_axis_title: Label for x-axis
        y_axis_title: Label for y-axis

    Returns:
        dict containing:
        - status: 'success' or 'error'
        - spreadsheet_id: The Google Sheets ID
        - spreadsheet_url: URL to view the spreadsheet with chart
        - message: Error message if status is 'error'

    Example:
        create_spreadsheet_with_chart(
            title="Breast Cancer Survival by Age",
            data={
                "Age Group": ["Under 50", "50-70", "Over 70"],
                "Patient Count": [234, 567, 345],
                "Avg Survival (days)": [1456, 1234, 987]
            },
            chart_type="COLUMN",
            chart_title="Survival by Age Group",
            x_axis_title="Age Group",
            y_axis_title="Average Survival (days)"
        )
    """
    sheets_service = _get_sheets_service()
    drive_service = _get_drive_service()

    if not sheets_service:
        return {
            "status": "error",
            "message": "Could not authenticate with Google Sheets API."
        }

    try:
        # Validate data
        if not data or not isinstance(data, dict):
            return {
                "status": "error",
                "message": "Data must be a non-empty dictionary with column headers as keys."
            }

        # Get column headers and ensure all columns have same length
        headers = list(data.keys())
        num_rows = len(data[headers[0]])
        for header in headers:
            if len(data[header]) != num_rows:
                return {
                    "status": "error",
                    "message": f"All data columns must have the same length. '{header}' has different length."
                }

        # Create the spreadsheet
        spreadsheet = sheets_service.spreadsheets().create(
            body={
                "properties": {"title": title},
                "sheets": [{"properties": {"title": "Data"}}]
            }
        ).execute()

        spreadsheet_id = spreadsheet["spreadsheetId"]
        sheet_id = spreadsheet["sheets"][0]["properties"]["sheetId"]

        # Prepare data for writing (headers + data rows)
        values = [headers]  # First row is headers
        for i in range(num_rows):
            row = [data[header][i] for header in headers]
            values.append(row)

        # Write data to the sheet
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="Data!A1",
            valueInputOption="RAW",
            body={"values": values}
        ).execute()

        # Map chart type string to Sheets API chart type
        chart_type_map = {
            "COLUMN": "COLUMN",
            "BAR": "BAR",
            "LINE": "LINE",
            "PIE": "PIE",
            "SCATTER": "SCATTER",
            "AREA": "AREA",
        }
        api_chart_type = chart_type_map.get(chart_type.upper(), "COLUMN")

        # Create the chart
        num_cols = len(headers)

        # Build chart request
        chart_request = {
            "addChart": {
                "chart": {
                    "position": {
                        "overlayPosition": {
                            "anchorCell": {
                                "sheetId": sheet_id,
                                "rowIndex": 1,
                                "columnIndex": num_cols + 1  # Place chart to the right of data
                            },
                            "offsetXPixels": 20,
                            "offsetYPixels": 20,
                            "widthPixels": 600,
                            "heightPixels": 400,
                        }
                    },
                    "spec": {
                        "title": chart_title or title,
                        "basicChart": {
                            "chartType": api_chart_type,
                            "legendPosition": "BOTTOM_LEGEND",
                            "axis": [
                                {
                                    "position": "BOTTOM_AXIS",
                                    "title": x_axis_title or headers[0]
                                },
                                {
                                    "position": "LEFT_AXIS",
                                    "title": y_axis_title or (headers[1] if len(headers) > 1 else "")
                                }
                            ],
                            "domains": [
                                {
                                    "domain": {
                                        "sourceRange": {
                                            "sources": [{
                                                "sheetId": sheet_id,
                                                "startRowIndex": 0,
                                                "endRowIndex": num_rows + 1,
                                                "startColumnIndex": 0,
                                                "endColumnIndex": 1
                                            }]
                                        }
                                    }
                                }
                            ],
                            "series": [
                                {
                                    "series": {
                                        "sourceRange": {
                                            "sources": [{
                                                "sheetId": sheet_id,
                                                "startRowIndex": 0,
                                                "endRowIndex": num_rows + 1,
                                                "startColumnIndex": col_idx,
                                                "endColumnIndex": col_idx + 1
                                            }]
                                        }
                                    },
                                    "targetAxis": "LEFT_AXIS"
                                }
                                for col_idx in range(1, num_cols)  # All columns except the first (domain)
                            ],
                            "headerCount": 1
                        }
                    }
                }
            }
        }

        # Handle PIE chart differently (no axes)
        if api_chart_type == "PIE":
            chart_request["addChart"]["chart"]["spec"] = {
                "title": chart_title or title,
                "pieChart": {
                    "legendPosition": "RIGHT_LEGEND",
                    "domain": {
                        "sourceRange": {
                            "sources": [{
                                "sheetId": sheet_id,
                                "startRowIndex": 0,
                                "endRowIndex": num_rows + 1,
                                "startColumnIndex": 0,
                                "endColumnIndex": 1
                            }]
                        }
                    },
                    "series": {
                        "sourceRange": {
                            "sources": [{
                                "sheetId": sheet_id,
                                "startRowIndex": 0,
                                "endRowIndex": num_rows + 1,
                                "startColumnIndex": 1,
                                "endColumnIndex": 2
                            }]
                        }
                    }
                }
            }

        # Execute the chart creation
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [chart_request]}
        ).execute()

        # Make the spreadsheet accessible via link
        if drive_service:
            try:
                drive_service.permissions().create(
                    fileId=spreadsheet_id,
                    body={"type": "anyone", "role": "reader"}
                ).execute()
            except Exception:
                pass  # Continue even if permission setting fails

        spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"

        return {
            "status": "success",
            "spreadsheet_id": spreadsheet_id,
            "spreadsheet_url": spreadsheet_url,
            "sheet_name": "Data",
            "chart_type": api_chart_type,
            "data_rows": num_rows,
            "data_columns": num_cols,
            "message": f"Created spreadsheet with {api_chart_type} chart. View at: {spreadsheet_url}"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to create spreadsheet with chart: {str(e)}"
        }


def add_chart_to_spreadsheet(
    spreadsheet_id: str,
    chart_type: str = "COLUMN",
    chart_title: str = "",
    data_range: str = "Data!A1:B10",
    x_axis_title: str = "",
    y_axis_title: str = "",
) -> dict:
    """
    Add a chart to an existing spreadsheet.

    Args:
        spreadsheet_id: The ID of the existing spreadsheet
        chart_type: Type of chart (COLUMN, BAR, LINE, PIE, SCATTER, AREA)
        chart_title: Title for the chart
        data_range: A1 notation for the data range (e.g., "Data!A1:C10")
        x_axis_title: Label for x-axis
        y_axis_title: Label for y-axis

    Returns:
        dict with status and chart details
    """
    sheets_service = _get_sheets_service()

    if not sheets_service:
        return {
            "status": "error",
            "message": "Could not authenticate with Google Sheets API."
        }

    try:
        # Get spreadsheet info to find sheet ID
        spreadsheet = sheets_service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()

        sheet_id = spreadsheet["sheets"][0]["properties"]["sheetId"]

        # Parse the data range to get dimensions
        # This is simplified - assumes format like "Sheet!A1:C10"
        range_parts = data_range.split("!")
        if len(range_parts) == 2:
            cell_range = range_parts[1]
        else:
            cell_range = range_parts[0]

        # Map chart type
        chart_type_map = {
            "COLUMN": "COLUMN",
            "BAR": "BAR",
            "LINE": "LINE",
            "PIE": "PIE",
            "SCATTER": "SCATTER",
            "AREA": "AREA",
        }
        api_chart_type = chart_type_map.get(chart_type.upper(), "COLUMN")

        # Create chart using the range
        chart_request = {
            "addChart": {
                "chart": {
                    "position": {
                        "overlayPosition": {
                            "anchorCell": {
                                "sheetId": sheet_id,
                                "rowIndex": 1,
                                "columnIndex": 5
                            },
                            "widthPixels": 600,
                            "heightPixels": 400,
                        }
                    },
                    "spec": {
                        "title": chart_title,
                        "basicChart": {
                            "chartType": api_chart_type,
                            "legendPosition": "BOTTOM_LEGEND",
                            "axis": [
                                {"position": "BOTTOM_AXIS", "title": x_axis_title},
                                {"position": "LEFT_AXIS", "title": y_axis_title}
                            ],
                            "domains": [
                                {
                                    "domain": {
                                        "sourceRange": {
                                            "sources": [{
                                                "sheetId": sheet_id,
                                                "startRowIndex": 0,
                                                "endRowIndex": 20,
                                                "startColumnIndex": 0,
                                                "endColumnIndex": 1
                                            }]
                                        }
                                    }
                                }
                            ],
                            "series": [
                                {
                                    "series": {
                                        "sourceRange": {
                                            "sources": [{
                                                "sheetId": sheet_id,
                                                "startRowIndex": 0,
                                                "endRowIndex": 20,
                                                "startColumnIndex": 1,
                                                "endColumnIndex": 2
                                            }]
                                        }
                                    },
                                    "targetAxis": "LEFT_AXIS"
                                }
                            ],
                            "headerCount": 1
                        }
                    }
                }
            }
        }

        result = sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [chart_request]}
        ).execute()

        return {
            "status": "success",
            "spreadsheet_id": spreadsheet_id,
            "spreadsheet_url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit",
            "chart_type": api_chart_type,
            "message": f"Added {api_chart_type} chart to spreadsheet."
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to add chart: {str(e)}"
        }


def get_spreadsheet_url(spreadsheet_id: str) -> dict:
    """
    Get the shareable URL for a spreadsheet.

    Args:
        spreadsheet_id: The Google Sheets spreadsheet ID

    Returns:
        dict with the spreadsheet URL and details
    """
    return {
        "status": "success",
        "spreadsheet_id": spreadsheet_id,
        "spreadsheet_url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit",
        "embed_url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/preview"
    }
