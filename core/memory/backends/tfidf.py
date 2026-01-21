"""
NEXUS V7.9 - TF-IDF Memory Backend (Phase 10f)

TF-IDF weighted Jaccard similarity retrieval.
Zero external dependencies - uses only standard library.

This is the fallback backend when BM25S is not installed.
"""

import math
import logging
from collections import defaultdict
from typing import List, Dict, Set, Any, Optional, TYPE_CHECKING

from .base import MemoryBackend

if TYPE_CHECKING:
    from ..types import Chunk


class TfidfBackend(MemoryBackend):
    """
    TF-IDF weighted Jaccard similarity retrieval backend.

    Scoring formula:
        Score = sum(idf[term] for term in intersection) / sum(idf[term] for term in query)

    Where:
        IDF(term) = log(N / (1 + df(term)))
        N = total chunks
        df = chunks containing term
    """

    def __init__(self):
        """Initialize the TF-IDF backend."""
        self._logger = logging.getLogger("nexus.memory.tfidf")
        self._idf: Dict[str, float] = {}
        self._index_built = False

    @property
    def name(self) -> str:
        """Get the backend name."""
        return "tfidf"

    @property
    def is_ready(self) -> bool:
        """Check if the index is built."""
        return self._index_built

    def build_index(self, chunks: List['Chunk']) -> None:
        """Builds IDF scores from the provided chunks.

        Calculates the Inverse Document Frequency (IDF) for every term found
        in the provided list of chunks. This index is used to weight terms
        during retrieval.

        Args:
            chunks: A list of Chunk objects to be indexed. If empty,
                the index is cleared.

        Returns:
            None

        Raises:
            None
        """
        if not chunks:
            self._idf = {}
            self._index_built = False
            return

        # Count document frequency for each term
        df: Dict[str, int] = defaultdict(int)
        for chunk in chunks:
            for term in chunk.terms:
                df[term] += 1

        # Calculate IDF: log(N / (1 + df))
        n = len(chunks)
        self._idf = {
            term: math.log(n / (1 + count))
            for term, count in df.items()
        }

        self._index_built = True
        self._logger.debug(f"TF-IDF index built: {len(self._idf)} terms from {n} chunks")

    def retrieve(
        self,
        query_terms: List[str],
        chunks: List['Chunk'],
        limit: int,
        min_score: float,
        raw_query: Optional[str] = None  # V7.9 Phase 10g: Ignored by sparse backends
    ) -> List['Chunk']:
        """Retrieves relevant chunks using TF-IDF weighted Jaccard similarity.

        Scores chunks based on the overlap of terms with the query, weighted by
        their IDF scores. Automatically builds the index if it hasn't been built yet.

        Args:
            query_terms: A list of pre-processed query terms.
            chunks: The full list of chunks to search against.
            limit: The maximum number of chunks to return.
            min_score: The minimum similarity score required for a chunk to be included.
            raw_query: The original query string (ignored by this backend).

        Returns:
            List['Chunk']: A list of the most relevant chunks, sorted by score
            in descending order.

        Raises:
            None
        """
        # Note: raw_query ignored - TF-IDF uses tokenized query_terms
        if not query_terms or not chunks:
            return []

        # Ensure index is built
        if not self._index_built:
            self.build_index(chunks)

        query_set = set(query_terms)

        # Score each chunk
        scored_chunks = []
        for chunk in chunks:
            score = self._score_chunk(query_set, chunk.terms)
            if score >= min_score:
                scored_chunks.append((score, chunk))

        # Sort by score descending
        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        # Return top chunks
        return [chunk for _, chunk in scored_chunks[:limit]]

    def _score_chunk(self, query_terms: Set[str], chunk_terms: Set[str]) -> float:
        """Calculates TF-IDF weighted Jaccard similarity.

        The score is computed as:
            Score = sum(idf[term] for term in intersection) / sum(idf[term] for term in query)

        Args:
            query_terms: Set of unique terms in the search query.
            chunk_terms: Set of unique terms in the chunk being scored.

        Returns:
            float: A similarity score relative to the query weight.

        Raises:
            None
        """
        intersection = query_terms & chunk_terms
        if not intersection:
            return 0.0

        # TF-IDF weighted score
        intersection_weight = sum(self._idf.get(term, 1.0) for term in intersection)
        query_weight = sum(self._idf.get(term, 1.0) for term in query_terms)

        if query_weight == 0:
            return 0.0

        return intersection_weight / query_weight

    def clear(self) -> None:
        """Clears the TF-IDF index.

        Resets the internal IDF dictionary and marks the index as unbuilt.

        Returns:
            None

        Raises:
            None
        """
        self._idf = {}
        self._index_built = False

    def get_info(self) -> Dict[str, Any]:
        """
        Get TF-IDF backend information.

        Returns:
            Dict[str, Any]: Backend status including:
                - backend: Name of the backend
                - terms_indexed: Number of terms in IDF map
                - index_built: Whether index is ready
                - dependencies: External dependency status
        """
        return {
            "backend": self.name,
            "terms_indexed": len(self._idf),
            "index_built": self._index_built,
            "dependencies": "none (stdlib only)"
        }
