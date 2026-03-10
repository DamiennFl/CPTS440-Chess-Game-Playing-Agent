from __future__ import annotations

import chess


def evaluate(board: chess.Board) -> float:
    """
    Return a heuristic score from White's perspective.

    Week 1 stub:
    - Terminal positions return large-magnitude scores.
    - Non-terminal positions return 0.0 (Week 2+ replaces this with material/positional terms).
    """
    if board.is_checkmate():
        return -1_000_000.0 if board.turn == chess.WHITE else 1_000_000.0
    if board.is_stalemate() or board.is_insufficient_material():
        return 0.0
    return 0.0

