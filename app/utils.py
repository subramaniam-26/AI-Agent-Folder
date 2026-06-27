# app/utils.py
"""Utility functions for the Soil Nutrient Analyzer.

Provides a canonical normalisation routine for soil type strings and a
pre-configured logger used by the MCP server modules for temporary debug
output (removed after verification).
"""

from __future__ import annotations

import logging
from typing import Final

# ---------------------------------------------------------------------------
# Logging configuration (debug level for temporary tracing)
# ---------------------------------------------------------------------------
logger: logging.Logger = logging.getLogger("soil_nutrient_analyzer")
if not logger.handlers:
    # Avoid duplicate handlers if the module is re-imported
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

# ---------------------------------------------------------------------------
# Soil type normalisation
# ---------------------------------------------------------------------------
# Explicit alias map for common variations that include the word "soil"
ALIAS_MAP: Final[dict[str, str]] = {
    "loam": "Red Loam",
    "saline": "Saline Soil",
    "peaty soil": "Peaty",
    "black cotton soil": "Black Cotton",
    "clay loam soil": "Clay Loam",
    "laterite soil": "Laterite",
    "sandy loam soil": "Sandy Loam",
    # Extend as needed
}


def normalize_soil_type(raw: str) -> str:
    """Return a canonical soil-type string.

    Steps performed:
    1. Strip surrounding whitespace.
    2. Lower-case the string for case-insensitive matching.
    3. Remove a trailing or leading ``"soil"`` token.
    4. Collapse multiple internal spaces.
    5. Translate explicit aliases via :data:`ALIAS_MAP`.
    6. Title-case the result to match the CSV values.
    """
    if not isinstance(raw, str):
        raise TypeError("soil_type must be a string")

    # 1-2. Normalise whitespace & case
    s = raw.strip().lower()

    # 3. Drop the word "soil" if it appears at the start or end
    if s.endswith(" soil"):
        s = s[: -len(" soil")]
    if s.startswith("soil "):
        s = s[len("soil ") :]

    # 4. Collapse any duplicate spaces
    s = " ".join(s.split())

    # 5. Alias lookup - exact match on the processed string
    canonical = ALIAS_MAP.get(s, s)

    # 6. Title-case for CSV compatibility (e.g. "black cotton" -> "Black Cotton")
    return canonical.title()
