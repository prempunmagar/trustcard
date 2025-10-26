"""
URL Extraction Utility

Extracts URLs from text content.
"""

import re
from typing import List


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text.

    Args:
        text: Text to search for URLs

    Returns:
        list: Found URLs
    """
    if not text:
        return []

    # URL regex pattern
    # Matches http:// and https:// URLs
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

    urls = re.findall(url_pattern, text)

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    return unique_urls


def extract_domains(text: str) -> List[str]:
    """
    Extract domain names from text.

    Args:
        text: Text to search

    Returns:
        list: Found domain names
    """
    urls = extract_urls(text)
    domains = []

    for url in urls:
        # Extract domain using regex
        domain_match = re.search(r'://([^/]+)', url)
        if domain_match:
            domain = domain_match.group(1)
            # Remove www prefix
            domain = re.sub(r'^www\.', '', domain)
            domains.append(domain)

    return domains
