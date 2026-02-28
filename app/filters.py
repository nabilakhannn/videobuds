"""Jinja2 custom filters — extracted from __init__.py for single-responsibility.

Register these on the Flask app via ``register_filters(app)``.
"""

from __future__ import annotations

import html as html_mod
import json
import re


# ---------------------------------------------------------------------------
# fromjson — parse a JSON string into a Python list/dict
# ---------------------------------------------------------------------------

def fromjson(value):
    """Parse a JSON string, returning ``[]`` on any failure."""
    try:
        return json.loads(value) if value else []
    except (json.JSONDecodeError, TypeError):
        return []


# ---------------------------------------------------------------------------
# simple_md — lightweight Markdown → HTML for Gemini-style output
# ---------------------------------------------------------------------------

def simple_md(text: str) -> str:
    """Convert simple Markdown to HTML (headers, bold, lists, line breaks).

    Handles Gemini-style output: ``**bold**``, ``*italic*``,
    ``*`` and ``-`` bullet lists (with optional indent), and
    ``1.`` / ``1)`` numbered lists.

    Input is HTML-escaped first to prevent XSS.
    """
    if not text:
        return ""
    text = html_mod.escape(text)

    # Headers: ### → <h3>, ## → <h2>
    text = re.sub(
        r'^### (.+)$',
        r'<h3 class="text-base font-semibold text-gray-900 dark:text-white mt-5 mb-2">\1</h3>',
        text, flags=re.MULTILINE,
    )
    text = re.sub(
        r'^## (.+)$',
        r'<h2 class="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">\1</h2>',
        text, flags=re.MULTILINE,
    )

    # Bold: **text**  (must run BEFORE italic and bullet detection)
    text = re.sub(
        r'\*\*(.+?)\*\*',
        r'<strong class="text-gray-900 dark:text-white font-semibold">\1</strong>',
        text,
    )

    # Unordered lists: lines starting with  -  or  *  (with optional indent)
    text = re.sub(
        r'^\s*[-*]\s+(.+)$',
        r'<li class="ml-4 pl-1 py-0.5 list-disc">\1</li>',
        text, flags=re.MULTILINE,
    )

    # Numbered lists: 1) item  or  1. item  (with optional indent)
    text = re.sub(
        r'^\s*(\d+)[\.\)]\s+(.+)$',
        r'<li class="ml-4 pl-1 py-0.5 list-decimal">\2</li>',
        text, flags=re.MULTILINE,
    )

    # Italic: *text* (safe to run after bullets are already <li>'d)
    text = re.sub(
        r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)',
        r'<em>\1</em>',
        text,
    )

    # Blank lines → paragraph breaks
    text = re.sub(r'\n\n+', '</p><p class="mb-2">', text)
    # Single newlines → <br>
    text = text.replace('\n', '<br>\n')
    # Wrap in <p>
    text = f'<p class="mb-2">{text}</p>'

    # Clean up: remove <br> right after / before block elements
    text = re.sub(r'(</h[23]>)<br>', r'\1', text)
    text = re.sub(r'(</li>)<br>', r'\1', text)
    text = re.sub(r'<br>\n(<h[23])', r'\n<\1', text)
    text = re.sub(r'<br>\n(<li)', r'\n<\1', text)
    return text


# ---------------------------------------------------------------------------
# Registration helper
# ---------------------------------------------------------------------------

def register_filters(app):
    """Register all custom Jinja2 filters on the Flask app."""
    app.jinja_env.filters["fromjson"] = fromjson
    app.jinja_env.filters["simple_md"] = simple_md
