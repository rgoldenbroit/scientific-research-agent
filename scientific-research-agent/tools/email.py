"""
Gmail tools for email drafting and sending.
Uses service account authentication (requires domain-wide delegation in Google Workspace).
"""
import os
import base64
import functools
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List

from google.auth import default


def safe_tool(func):
    """Decorator that ensures a tool ALWAYS returns a dict response."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            if not isinstance(result, dict):
                return {"status": "success", "result": result}
            return result
        except Exception as e:
            return {
                "status": "error",
                "message": f"⚠️ TOOL ERROR in {func.__name__}: {str(e)}",
                "exception_type": type(e).__name__
            }
    return wrapper
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Scopes required for Gmail access
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
]

# Store last auth error for debugging
_last_auth_error = None


def _get_credentials():
    """Get Google credentials for Gmail API with domain-wide delegation support."""
    global _last_auth_error

    # Get the email to impersonate from environment (required for domain-wide delegation)
    impersonate_email = os.environ.get("GMAIL_IMPERSONATE_EMAIL")

    try:
        credentials, project = default(scopes=SCOPES)

        # For service accounts, add impersonation if configured
        if impersonate_email and hasattr(credentials, 'with_subject'):
            credentials = credentials.with_subject(impersonate_email)

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
                # Add impersonation for service account key auth
                if impersonate_email:
                    credentials = credentials.with_subject(impersonate_email)
                _last_auth_error = None
                return credentials
            except Exception as e2:
                _last_auth_error = f"Default auth failed: {_last_auth_error}. SA key failed: {str(e2)}"
        return None


def _get_gmail_service():
    """Get an authenticated Gmail service."""
    credentials = _get_credentials()
    if not credentials:
        return None
    try:
        return build("gmail", "v1", credentials=credentials)
    except Exception:
        return None


def _create_message(
    to: str,
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    is_html: bool = False,
) -> dict:
    """Create a message for the Gmail API."""
    if is_html:
        message = MIMEMultipart("alternative")
        message.attach(MIMEText(body, "html"))
    else:
        message = MIMEText(body)

    message["to"] = to
    message["subject"] = subject

    if cc:
        message["cc"] = ", ".join(cc)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return {"raw": raw}


@safe_tool
def send_email(
    to: str,
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    is_html: bool = False,
) -> dict:
    """
    Send an email using Gmail API.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body content (plain text or HTML)
        cc: Optional list of CC recipients
        is_html: Whether the body is HTML formatted (default: False)

    Returns:
        dict containing:
        - status: 'success' or 'error'
        - message_id: Gmail message ID (if successful)
        - thread_id: Gmail thread ID (if successful)
    """
    gmail_service = _get_gmail_service()

    if not gmail_service:
        return {
            "status": "error",
            "message": f"Could not authenticate with Gmail API. {_last_auth_error or 'Check service account permissions.'}"
        }

    try:
        message = _create_message(to, subject, body, cc, is_html)
        sent_message = gmail_service.users().messages().send(
            userId="me",
            body=message
        ).execute()

        return {
            "status": "success",
            "message_id": sent_message.get("id"),
            "thread_id": sent_message.get("threadId"),
            "recipient": to,
            "subject": subject,
        }

    except Exception as e:
        error_msg = str(e)
        # Provide helpful error messages for common issues
        if "Precondition check failed" in error_msg:
            error_msg = "Gmail API requires domain-wide delegation. Set GMAIL_IMPERSONATE_EMAIL env var and configure delegation in Google Workspace Admin."
        elif "insufficientPermissions" in error_msg:
            error_msg = "Gmail API permissions not configured. Service account needs domain-wide delegation with Gmail send scope."
        elif "accessNotConfigured" in error_msg:
            error_msg = "Gmail API not enabled in GCP project. Enable it at console.cloud.google.com/apis/library/gmail.googleapis.com"

        return {
            "status": "error",
            "message": error_msg
        }


@safe_tool
def create_draft(
    to: str,
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    is_html: bool = False,
) -> dict:
    """
    Create an email draft in Gmail (does not send).

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body content (plain text or HTML)
        cc: Optional list of CC recipients
        is_html: Whether the body is HTML formatted (default: False)

    Returns:
        dict containing:
        - status: 'success' or 'error'
        - draft_id: Gmail draft ID (if successful)
        - draft_url: URL to open the draft in Gmail
    """
    gmail_service = _get_gmail_service()

    if not gmail_service:
        return {
            "status": "error",
            "message": f"Could not authenticate with Gmail API. {_last_auth_error or 'Check service account permissions.'}"
        }

    try:
        message = _create_message(to, subject, body, cc, is_html)
        draft = gmail_service.users().drafts().create(
            userId="me",
            body={"message": message}
        ).execute()

        draft_id = draft.get("id")
        # Gmail draft URL format
        draft_url = f"https://mail.google.com/mail/u/0/#drafts?compose={draft_id}"

        return {
            "status": "success",
            "draft_id": draft_id,
            "draft_url": draft_url,
            "recipient": to,
            "subject": subject,
        }

    except Exception as e:
        error_msg = str(e)
        if "Precondition check failed" in error_msg:
            error_msg = "Gmail API requires domain-wide delegation. Set GMAIL_IMPERSONATE_EMAIL env var and configure delegation in Google Workspace Admin."
        elif "insufficientPermissions" in error_msg:
            error_msg = "Gmail API permissions not configured. Service account needs domain-wide delegation."
        elif "accessNotConfigured" in error_msg:
            error_msg = "Gmail API not enabled in GCP project."

        return {
            "status": "error",
            "message": error_msg
        }


@safe_tool
def draft_email_content(
    recipient_name: str,
    recipient_email: str,
    team_name: str,
    research_summary: str,
    researcher_name: Optional[str] = None,
    action_items: Optional[List[str]] = None,
) -> dict:
    """
    Generate professional email content for reaching out to an organizational team.
    This is a helper function that creates well-formatted email text.

    Args:
        recipient_name: Name of the person/team being contacted
        recipient_email: Email address of the recipient
        team_name: Name of the team (e.g., "Cancer Research Institute")
        research_summary: Brief summary of the research findings/context
        researcher_name: Optional name of the researcher sending the email
        action_items: Optional list of specific requests/questions

    Returns:
        dict containing:
        - status: 'success'
        - to: Recipient email
        - subject: Generated subject line
        - body: Generated email body
        - body_html: HTML formatted version
    """
    # Generate subject line
    subject = f"Research Collaboration Inquiry - {team_name}"

    # Build plain text body
    greeting = f"Dear {recipient_name}," if recipient_name else f"Dear {team_name} Team,"

    body_parts = [
        greeting,
        "",
        "I am reaching out regarding potential collaboration and guidance based on recent research findings.",
        "",
        "**Research Summary:**",
        research_summary,
        "",
    ]

    if action_items:
        body_parts.append("**Specific Questions/Requests:**")
        for item in action_items:
            body_parts.append(f"- {item}")
        body_parts.append("")

    body_parts.extend([
        "I would appreciate the opportunity to discuss how your team might assist with next steps.",
        "",
        "Thank you for your time and consideration.",
        "",
        "Best regards,",
        researcher_name or "[Your Name]",
    ])

    body = "\n".join(body_parts)

    # Build HTML body
    html_parts = [
        f"<p>{greeting}</p>",
        "<p>I am reaching out regarding potential collaboration and guidance based on recent research findings.</p>",
        "<p><strong>Research Summary:</strong></p>",
        f"<p>{research_summary}</p>",
    ]

    if action_items:
        html_parts.append("<p><strong>Specific Questions/Requests:</strong></p>")
        html_parts.append("<ul>")
        for item in action_items:
            html_parts.append(f"<li>{item}</li>")
        html_parts.append("</ul>")

    html_parts.extend([
        "<p>I would appreciate the opportunity to discuss how your team might assist with next steps.</p>",
        "<p>Thank you for your time and consideration.</p>",
        "<p>Best regards,<br>",
        f"{researcher_name or '[Your Name]'}</p>",
    ])

    body_html = "\n".join(html_parts)

    return {
        "status": "success",
        "to": recipient_email,
        "subject": subject,
        "body": body,
        "body_html": body_html,
        "team_name": team_name,
    }
