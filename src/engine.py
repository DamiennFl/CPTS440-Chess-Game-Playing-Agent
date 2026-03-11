from __future__ import annotations

from typing import Optional

import chess

from src.search import SearchResult, choose_move as search_choose_move


def choose_move(
    board: chess.Board,
    *,
    time_limit: Optional[float] = None,
    depth: Optional[int] = None,
) -> SearchResult:
    """Top-level engine hook for move selection."""
    return search_choose_move(board, time_limit=time_limit, depth=depth)

