"""Synthesis - Cross-reference facts and generate memo sections"""

from .enrichment import enrich_facts
from .sections import generate_sections

__all__ = ["enrich_facts", "generate_sections"]
