from __future__ import annotations

from typing import Optional

import chess


def order_moves(board: chess.Board) -> list[chess.Move]:
    """
    Week 1 simple move ordering:
    prioritize captures/checks before quiet moves.
    """
    legal = list(board.legal_moves)
    legal.sort(
        key=lambda m: (
            board.is_capture(m),
            board.gives_check(m),
        ),
        reverse=True,
    )
    return legal


def choose_move(
    board: chess.Board,
    *,
    time_limit: Optional[float] = None,
    depth: Optional[int] = None,
) -> Optional[chess.Move]:
    """
    Week 1 placeholder chooser to support UI wiring.
    Returns the highest-priority legal move by ordering heuristic.
    """
    del time_limit, depth
    moves = order_moves(board)
    return moves[0] if moves else None

