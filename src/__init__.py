"""
L'œil Research Memo Generator

Generate investment research memos from public data sources.
Built on LangGraph for Sapphire Ventures.
"""

from .pipeline import generate_memo, generate_memo_sync, build_pipeline
from .state import MemoState

__all__ = [
    "generate_memo",
    "generate_memo_sync", 
    "build_pipeline",
    "MemoState",
]

__version__ = "0.1.0"
