import re
from typing import TypedDict


class ExtractionResult(TypedDict):
    """Structure for extraction results"""

    hashtags: list[str]
    action_items: list[str]


def extract_hashtags(text: str) -> list[str]:
    """Extract hashtags from text.

    Finds words starting with # (e.g., #python, #todo)
    Returns unique hashtags without the # prefix.
    """
    # Match hashtags: # followed by alphanumeric and underscores
    pattern = r"#([a-zA-Z0-9_]+)"
    matches = re.findall(pattern, text)
    # Return unique hashtags while preserving order
    seen = set()
    result = []
    for tag in matches:
        tag_lower = tag.lower()
        if tag_lower not in seen:
            seen.add(tag_lower)
            result.append(tag_lower)
    return result


def extract_action_items(text: str) -> list[str]:
    """Extract action items from text.

    Supports multiple formats:
    - Markdown checkboxes: - [ ] task or - [x] task
    - Exclamation marks: - Ship it!
    - TODO prefix: - TODO: write tests
    """
    items = []

    # Extract markdown checkbox items: - [ ] or - [x]
    checkbox_pattern = r"^\s*-\s*\[[\sx]\]\s*(.+)$"
    for line in text.splitlines():
        match = re.match(checkbox_pattern, line, re.IGNORECASE)
        if match:
            item = match.group(1).strip()
            if item:
                items.append(item)

    # Also extract old format (lines ending with ! or starting with TODO:)
    lines = [line.strip("- ") for line in text.splitlines() if line.strip()]
    for line in lines:
        if (line.endswith("!") or line.lower().startswith("todo:")) and line not in items:
            items.append(line)

    return items


def extract_all(text: str) -> ExtractionResult:
    """Extract both hashtags and action items from text."""
    return ExtractionResult(
        hashtags=extract_hashtags(text), action_items=extract_action_items(text)
    )
