"""
Google Docs tools for document creation and editing.
Uses service account authentication for simplified setup.
"""
import os
from typing import Optional, List

from google.oauth2 import service_account
from googleapiclient.discovery import build

# Optional: Default folder ID for storing created documents
DRIVE_FOLDER_ID = os.environ.get("AGENT_DRIVE_FOLDER_ID", "")

# Scopes required for Docs and Drive access
SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file"
]


def _get_docs_service():
    """Get an authenticated Google Docs service."""
    try:
        from google.auth import default
        credentials, project = default(scopes=SCOPES)
        return build("docs", "v1", credentials=credentials)
    except Exception:
        return None


def _get_drive_service():
    """Get an authenticated Google Drive service."""
    try:
        from google.auth import default
        credentials, project = default(scopes=SCOPES)
        return build("drive", "v3", credentials=credentials)
    except Exception:
        return None


def create_google_doc(
    title: str,
    content: str = "",
    folder_id: Optional[str] = None
) -> dict:
    """
    Create a new Google Doc with optional initial content.

    Args:
        title: Title of the document
        content: Optional initial content (plain text, will be added as body text)
        folder_id: Optional Drive folder ID to create the doc in.
                   Uses AGENT_DRIVE_FOLDER_ID env var if not provided.

    Returns:
        dict containing:
        - status: 'success' or 'error'
        - doc_id: The Google Docs document ID
        - doc_url: URL to open the document
        - title: Document title
    """
    docs_service = _get_docs_service()
    drive_service = _get_drive_service()

    if not docs_service:
        return {
            "status": "error",
            "message": "Could not authenticate with Google Docs."
        }

    try:
        # Create the document
        document = docs_service.documents().create(body={"title": title}).execute()
        doc_id = document["documentId"]

        # Add initial content if provided
        if content:
            requests = [
                {
                    "insertText": {
                        "location": {"index": 1},
                        "text": content
                    }
                }
            ]
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={"requests": requests}
            ).execute()

        # Move to folder if specified
        target_folder = folder_id or DRIVE_FOLDER_ID
        if target_folder and drive_service:
            # Get current parents
            file = drive_service.files().get(
                fileId=doc_id,
                fields="parents"
            ).execute()
            previous_parents = ",".join(file.get("parents", []))

            # Move to target folder
            drive_service.files().update(
                fileId=doc_id,
                addParents=target_folder,
                removeParents=previous_parents,
                fields="id, parents"
            ).execute()

        # Make document accessible via link
        if drive_service:
            drive_service.permissions().create(
                fileId=doc_id,
                body={"type": "anyone", "role": "reader"}
            ).execute()

        return {
            "status": "success",
            "doc_id": doc_id,
            "doc_url": f"https://docs.google.com/document/d/{doc_id}/edit",
            "title": title
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def append_to_doc(doc_id: str, content: str, add_newline: bool = True) -> dict:
    """
    Append text content to an existing Google Doc.

    Args:
        doc_id: The Google Docs document ID
        content: Text content to append
        add_newline: Whether to add a newline before the content (default: True)

    Returns:
        dict with status and updated document info
    """
    docs_service = _get_docs_service()

    if not docs_service:
        return {
            "status": "error",
            "message": "Could not authenticate with Google Docs."
        }

    try:
        # Get document to find end index
        document = docs_service.documents().get(documentId=doc_id).execute()
        end_index = document["body"]["content"][-1]["endIndex"] - 1

        # Prepare text to insert
        text_to_insert = ("\n" if add_newline else "") + content

        requests = [
            {
                "insertText": {
                    "location": {"index": end_index},
                    "text": text_to_insert
                }
            }
        ]

        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": requests}
        ).execute()

        return {
            "status": "success",
            "doc_id": doc_id,
            "doc_url": f"https://docs.google.com/document/d/{doc_id}/edit",
            "content_added": len(content)
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def embed_image_in_doc(
    doc_id: str,
    image_url: str,
    width: Optional[int] = None,
    height: Optional[int] = None
) -> dict:
    """
    Embed an image into a Google Doc at the end of the document.
    The image must be accessible via URL (e.g., from Google Drive with sharing enabled).

    Args:
        doc_id: The Google Docs document ID
        image_url: URL of the image to embed (must be publicly accessible or a Drive link)
        width: Optional width in points (72 points = 1 inch)
        height: Optional height in points

    Returns:
        dict with status and document info
    """
    docs_service = _get_docs_service()

    if not docs_service:
        return {
            "status": "error",
            "message": "Could not authenticate with Google Docs."
        }

    try:
        # Get document to find end index
        document = docs_service.documents().get(documentId=doc_id).execute()
        end_index = document["body"]["content"][-1]["endIndex"] - 1

        # Build the image insert request
        image_request = {
            "insertInlineImage": {
                "location": {"index": end_index},
                "uri": image_url,
            }
        }

        # Add optional size constraints
        if width or height:
            object_size = {}
            if width:
                object_size["width"] = {"magnitude": width, "unit": "PT"}
            if height:
                object_size["height"] = {"magnitude": height, "unit": "PT"}
            image_request["insertInlineImage"]["objectSize"] = object_size

        # First add a newline, then the image
        requests = [
            {
                "insertText": {
                    "location": {"index": end_index},
                    "text": "\n\n"
                }
            }
        ]

        # Execute newline insert first
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": requests}
        ).execute()

        # Get updated end index
        document = docs_service.documents().get(documentId=doc_id).execute()
        end_index = document["body"]["content"][-1]["endIndex"] - 1

        # Now insert the image
        image_request["insertInlineImage"]["location"]["index"] = end_index
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": [image_request]}
        ).execute()

        return {
            "status": "success",
            "doc_id": doc_id,
            "doc_url": f"https://docs.google.com/document/d/{doc_id}/edit",
            "image_embedded": True,
            "image_url": image_url
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def add_heading_to_doc(
    doc_id: str,
    heading_text: str,
    heading_level: int = 1
) -> dict:
    """
    Add a heading to a Google Doc.

    Args:
        doc_id: The Google Docs document ID
        heading_text: Text for the heading
        heading_level: Heading level (1-6, where 1 is largest)

    Returns:
        dict with status and document info
    """
    docs_service = _get_docs_service()

    if not docs_service:
        return {
            "status": "error",
            "message": "Could not authenticate with Google Docs."
        }

    try:
        # Get document to find end index
        document = docs_service.documents().get(documentId=doc_id).execute()
        end_index = document["body"]["content"][-1]["endIndex"] - 1

        # Map heading level to named style
        heading_styles = {
            1: "HEADING_1",
            2: "HEADING_2",
            3: "HEADING_3",
            4: "HEADING_4",
            5: "HEADING_5",
            6: "HEADING_6"
        }
        style = heading_styles.get(heading_level, "HEADING_1")

        # Insert text
        text_to_insert = "\n" + heading_text + "\n"

        requests = [
            {
                "insertText": {
                    "location": {"index": end_index},
                    "text": text_to_insert
                }
            },
            {
                "updateParagraphStyle": {
                    "range": {
                        "startIndex": end_index + 1,
                        "endIndex": end_index + 1 + len(heading_text)
                    },
                    "paragraphStyle": {
                        "namedStyleType": style
                    },
                    "fields": "namedStyleType"
                }
            }
        ]

        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": requests}
        ).execute()

        return {
            "status": "success",
            "doc_id": doc_id,
            "doc_url": f"https://docs.google.com/document/d/{doc_id}/edit",
            "heading_added": heading_text
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
