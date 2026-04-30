from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import chess

from src.search import SearchResult, choose_move as search_choose_move


def choose_move(
    board: chess.Board,
    *,
    time_limit: Optional[float] = None,
    depth: Optional[int] = None,
    use_alpha_beta: bool = True,
) -> SearchResult:
    """Top-level engine hook for move selection."""
    # Week 5/6 passthrough: preserve search configuration for experiments
    # (fixed depth vs time-limited iterative deepening, and AB vs minimax).
    return search_choose_move(
        board,
        time_limit=time_limit,
        depth=depth,
        use_alpha_beta=use_alpha_beta,
    )


@dataclass
class PlayRecord:
    """Snapshot of a single half-move in a game."""

    fen_before: str
    move_uci: str
    score: float
    nodes: int
    # Week 6 telemetry: per-move search time for experiment and replay reporting.
    elapsed: float = 0.0


@dataclass
class GameRecord:
    """Complete record of an AI-vs-AI game."""

    plies: list[PlayRecord] = field(default_factory=list)
    final_fen: str = chess.STARTING_FEN
    result: str = "*"


def play_game(
    *,
    depth: int = 2,
    time_limit: Optional[float] = None,
    use_alpha_beta: bool = True,
    max_moves: int = 150,
    fen: str = chess.STARTING_FEN,
) -> GameRecord:
    """
    Run an AI-vs-AI game and return a structured record.

    Args:
        depth: search depth in plies for both sides.
        time_limit: optional time budget per move in seconds.
        use_alpha_beta: choose between alpha-beta pruning and plain minimax.
        max_moves: maximum number of full moves before stopping.
        fen: starting position in FEN notation.

    Returns:
        A GameRecord containing per-ply snapshots and the final result.
    """
    board = chess.Board(fen)
    record = GameRecord()

    for _ in range(max_moves * 2):  # max_moves full moves = 2x half-moves
        if board.is_game_over(claim_draw=True):
            break

        result = choose_move(
            board,
            depth=depth,
            time_limit=time_limit,
            use_alpha_beta=use_alpha_beta,
        )
        if result.move is None or board.can_claim_draw():
            break

        record.plies.append(
            PlayRecord(
                fen_before=board.fen(),
                move_uci=result.move.uci(),
                score=result.score,
                nodes=result.nodes,
                elapsed=result.elapsed,
            )
        )
        board.push(result.move)

    record.final_fen = board.fen()
    record.result = board.result(claim_draw=True) if board.is_game_over(claim_draw=True) else "*"
    return record

