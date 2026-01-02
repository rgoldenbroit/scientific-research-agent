"""
Google Drive tools for file storage and sharing.
Uses service account authentication for simplified setup.
"""
import base64
import os
from typing import Optional

from google.auth import default
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload

# Optional: Folder ID for storing all agent-generated files
DRIVE_FOLDER_ID = os.environ.get("AGENT_DRIVE_FOLDER_ID", "")

# Scopes required for Drive access
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Store last auth error for debugging
_last_auth_error = None


def _get_credentials():
    """Get Google credentials, handling various authentication scenarios."""
    global _last_auth_error
    try:
        credentials, project = default(scopes=SCOPES)
        _last_auth_error = None
        return credentials
    except Exception as e:
        _last_auth_error = str(e)
        sa_key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if sa_key_path and os.path.exists(sa_key_path):
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    sa_key_path, scopes=SCOPES
                )
                _last_auth_error = None
                return credentials
            except Exception as e2:
                _last_auth_error = f"Default auth failed: {_last_auth_error}. SA key failed: {str(e2)}"
        return None


def _get_drive_service():
    """
    Get an authenticated Google Drive service.
    Uses Application Default Credentials (ADC) which works with:
    - Service accounts in GCP
    - User credentials via gcloud auth application-default login
    """
    credentials = _get_credentials()
    if not credentials:
        return None
    try:
        return build("drive", "v3", credentials=credentials)
    except Exception as e:
        return None


def save_to_drive(
    file_content: bytes,
    filename: str,
    mime_type: str,
    folder_id: Optional[str] = None,
    description: Optional[str] = None
) -> dict:
    """
    Save a file to Google Drive and return the shareable URL.

    Args:
        file_content: The file content as bytes (e.g., PNG image bytes)
        filename: Name for the file in Drive
        mime_type: MIME type of the file (e.g., 'image/png', 'application/pdf')
        folder_id: Optional Drive folder ID. Uses AGENT_DRIVE_FOLDER_ID env var if not provided.
        description: Optional description for the file

    Returns:
        dict containing:
        - status: 'success' or 'error'
        - file_id: The Google Drive file ID
        - web_view_link: URL to view the file in browser
        - web_content_link: Direct download URL
        - message: Error message if status is 'error'
    """
    service = _get_drive_service()
    if not service:
        return {
            "status": "error",
            "message": "Could not authenticate with Google Drive. Ensure credentials are configured."
        }

    try:
        # Use provided folder_id or fall back to environment variable
        target_folder = folder_id or DRIVE_FOLDER_ID

        # File metadata
        file_metadata = {
            "name": filename,
        }
        if target_folder:
            file_metadata["parents"] = [target_folder]
        if description:
            file_metadata["description"] = description

        # Create media upload
        media = MediaInMemoryUpload(file_content, mimetype=mime_type, resumable=True)

        # Upload file
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, name, webViewLink, webContentLink"
        ).execute()

        # Make file accessible via link
        service.permissions().create(
            fileId=file["id"],
            body={"type": "anyone", "role": "reader"}
        ).execute()

        return {
            "status": "success",
            "file_id": file["id"],
            "filename": file["name"],
            "web_view_link": file.get("webViewLink", f"https://drive.google.com/file/d/{file['id']}/view"),
            "web_content_link": file.get("webContentLink", f"https://drive.google.com/uc?id={file['id']}")
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def save_image_to_drive(
    image_base64: str,
    filename: str,
    folder_id: Optional[str] = None,
    description: Optional[str] = None
) -> dict:
    """
    Save a base64-encoded image to Google Drive.
    Convenience wrapper for save_to_drive for image files.

    Args:
        image_base64: Base64-encoded image data (without data URL prefix)
        filename: Name for the image file (should include extension, e.g., 'chart.png')
        folder_id: Optional Drive folder ID
        description: Optional description for the file

    Returns:
        dict with file info (same as save_to_drive)
    """
    try:
        # Decode base64 image
        image_bytes = base64.b64decode(image_base64)

        # Determine mime type from filename
        ext = filename.lower().split(".")[-1]
        mime_types = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
            "svg": "image/svg+xml",
            "pdf": "application/pdf"
        }
        mime_type = mime_types.get(ext, "image/png")

        return save_to_drive(
            file_content=image_bytes,
            filename=filename,
            mime_type=mime_type,
            folder_id=folder_id,
            description=description
        )

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to decode or save image: {str(e)}"
        }


def get_drive_file_url(file_id: str) -> dict:
    """
    Get the shareable URL for a file already in Google Drive.

    Args:
        file_id: The Google Drive file ID

    Returns:
        dict containing:
        - status: 'success' or 'error'
        - web_view_link: URL to view the file in browser
        - web_content_link: Direct download URL
        - name: File name
        - mime_type: File MIME type
    """
    service = _get_drive_service()
    if not service:
        return {
            "status": "error",
            "message": "Could not authenticate with Google Drive."
        }

    try:
        file = service.files().get(
            fileId=file_id,
            fields="id, name, mimeType, webViewLink, webContentLink"
        ).execute()

        return {
            "status": "success",
            "file_id": file["id"],
            "name": file["name"],
            "mime_type": file["mimeType"],
            "web_view_link": file.get("webViewLink", f"https://drive.google.com/file/d/{file_id}/view"),
            "web_content_link": file.get("webContentLink", f"https://drive.google.com/uc?id={file_id}")
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def list_drive_files(folder_id: Optional[str] = None, max_results: int = 20) -> dict:
    """
    List files in a Google Drive folder.

    Args:
        folder_id: Optional folder ID. Uses AGENT_DRIVE_FOLDER_ID if not provided.
        max_results: Maximum number of files to return (default: 20)

    Returns:
        dict containing list of files with their IDs and URLs
    """
    service = _get_drive_service()
    if not service:
        return {
            "status": "error",
            "message": "Could not authenticate with Google Drive."
        }

    try:
        target_folder = folder_id or DRIVE_FOLDER_ID

        # Build query
        query = f"'{target_folder}' in parents" if target_folder else None

        results = service.files().list(
            q=query,
            pageSize=max_results,
            fields="files(id, name, mimeType, webViewLink, createdTime)"
        ).execute()

        files = results.get("files", [])

        return {
            "status": "success",
            "folder_id": target_folder,
            "file_count": len(files),
            "files": [
                {
                    "file_id": f["id"],
                    "name": f["name"],
                    "mime_type": f["mimeType"],
                    "web_view_link": f.get("webViewLink"),
                    "created_time": f.get("createdTime")
                }
                for f in files
            ]
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
