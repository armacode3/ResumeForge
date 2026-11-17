"""Shared literal-span policy for retrieval and its source-backed annotations."""

import re


def literal_span(needle: str, haystack: str) -> str | None:
    # Keep +/# attached to technology names: C is not C++/C#, Java is not JavaScript.
    if len(needle) > len(haystack):
        return None
    found = re.search(r"(?<![\w+#])" + re.escape(needle) + r"(?![\w+#])", haystack, re.IGNORECASE)
    return found.group() if found else None
