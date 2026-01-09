"""
Guidance tools for organizational contact lookup and domain matching.
Provides researchers with next steps and relevant team contacts based on their research domain.
"""
import os
import functools
from typing import Optional, List, Dict, Any

import yaml


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

# Path to contacts configuration (relative to this file)
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "contacts.yaml")


def _load_contacts_config() -> Dict[str, Any]:
    """Load the contacts configuration from YAML file."""
    try:
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {"default": None, "domains": {}}
    except yaml.YAMLError as e:
        return {"error": f"Failed to parse contacts config: {str(e)}"}


def _match_domain(text: str, config: Dict[str, Any]) -> List[str]:
    """
    Match text against domain keywords.
    Returns list of matching domain names, sorted by relevance (keyword count).
    """
    text_lower = text.lower()
    matches = []

    for domain_name, domain_config in config.get("domains", {}).items():
        keywords = domain_config.get("keywords", [])
        match_count = sum(1 for kw in keywords if kw.lower() in text_lower)
        if match_count > 0:
            matches.append((domain_name, match_count))

    # Sort by match count descending
    matches.sort(key=lambda x: x[1], reverse=True)
    return [m[0] for m in matches]


def _format_guidance_text(domains: List[str], contacts: List[Dict]) -> str:
    """Format contacts into readable guidance text for documents."""
    if not contacts:
        return "No specific organizational contacts identified for this research area."

    domain_str = ", ".join(domains) if domains else "general research"
    lines = [
        "Organizational Next Steps",
        "",
        f"Based on your research in {domain_str}, the following teams may be helpful:",
        "",
    ]

    for i, contact in enumerate(contacts, 1):
        lines.append(f"{i}. {contact.get('team_name', 'Unknown Team')}")
        lines.append(f"Purpose: {contact.get('purpose', 'N/A')}")
        lines.append(f"Contact: {contact.get('email', 'N/A')}")
        if contact.get("link"):
            lines.append(f"More Info: {contact['link']}")
        lines.append("")
        lines.append("Recommended Actions:")
        for action in contact.get("action_items", []):
            lines.append(f"  - {action}")
        lines.append("")

    return "\n".join(lines)


@safe_tool
def get_organizational_contacts(
    research_context: str,
    domains: Optional[List[str]] = None,
) -> dict:
    """
    Get organizational contacts and next steps based on research context.

    Args:
        research_context: Description of the research (analysis summary,
                         hypothesis text, or keywords)
        domains: Optional list of specific domains to include (e.g., ["cancer", "genomics"])
                If not provided, domains are inferred from research_context

    Returns:
        dict containing:
        - status: 'success' or 'error'
        - matched_domains: List of domains that matched
        - contacts: List of contact entries with team_name, purpose, email, link, action_items
        - guidance_text: Formatted text suitable for appending to a document
    """
    config = _load_contacts_config()

    if "error" in config:
        return {"status": "error", "message": config["error"]}

    # Determine which domains to use
    if domains:
        matched_domains = [d for d in domains if d in config.get("domains", {})]
    else:
        matched_domains = _match_domain(research_context, config)

    # Collect contacts from matched domains
    contacts = []
    seen_teams = set()  # Avoid duplicates if domains overlap
    for domain in matched_domains:
        domain_contacts = config.get("domains", {}).get(domain, {}).get("contacts", [])
        for contact in domain_contacts:
            team_name = contact.get("team_name")
            if team_name not in seen_teams:
                contact_entry = contact.copy()
                contact_entry["domain"] = domain
                contacts.append(contact_entry)
                seen_teams.add(team_name)

    # Add default contact if no matches
    if not contacts and config.get("default"):
        default_contact = config["default"].copy()
        default_contact["domain"] = "default"
        contacts.append(default_contact)

    # Generate formatted guidance text
    guidance_text = _format_guidance_text(matched_domains, contacts)

    return {
        "status": "success",
        "matched_domains": matched_domains,
        "contacts": contacts,
        "guidance_text": guidance_text,
    }


@safe_tool
def list_available_domains() -> dict:
    """
    List all available research domains in the configuration.

    Returns:
        dict containing:
        - status: 'success' or 'error'
        - domains: List of domain info with name, keywords, and contact count
    """
    config = _load_contacts_config()

    if "error" in config:
        return {"status": "error", "message": config["error"]}

    domains = []
    for domain_name, domain_config in config.get("domains", {}).items():
        domains.append(
            {
                "name": domain_name,
                "keywords": domain_config.get("keywords", []),
                "contact_count": len(domain_config.get("contacts", [])),
            }
        )

    return {"status": "success", "domains": domains}
