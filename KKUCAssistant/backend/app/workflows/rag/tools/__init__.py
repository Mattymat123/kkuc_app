"""
RAG Tools
Tools specific to the RAG workflow
"""
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Represents a search result from vector/BM25 search"""
    content: str
    source_url: str
    page_title: str
    score: float
