from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import chess

from src import eval


@dataclass(frozen=True)
class SearchResult:
    """Immutable container for the output of a search."""

    move: Optional[chess.Move]
    score: float
    nodes: int
    depth: int


def order_moves(board: chess.Board) -> list[chess.Move]:
    """
    Simple move ordering:
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


# Default search depth (plies). Adjust as needed or override via choose_move(..., depth=...).
DEFAULT_DEPTH = 2


def minimax(
    board: chess.Board,
    depth: int,
    maximizing_player: bool,
    *,
    node_counter: Optional[list[int]] = None,
) -> Tuple[float, Optional[chess.Move]]:
    """
    Depth-limited minimax search (no alpha-beta yet).

    Args:
        board: current chess position (mutated via push/pop during search).
        depth: remaining plies to explore (0 == evaluate current node).
        maximizing_player: True if the side to move is treated as the maximizing player.
        node_counter: optional single-element list used to count visited nodes for debugging/metrics.

    Returns:
        (score, best_move) where score is from White's perspective.
        best_move is None for leaf/terminal nodes.
    """
    if node_counter is not None:
        node_counter[0] += 1

    # Base case: depth exhausted or terminal position.
    if depth == 0 or board.is_game_over():
        return eval.evaluate(board), None

    legal_moves = order_moves(board)
    if not legal_moves:
        # No legal moves but not flagged as game_over (rare case); treat as leaf.
        return eval.evaluate(board), None

    best_move = None
    if maximizing_player:
        best_score = float("-inf") # Initialize to worst case for maximizing player.
        for move in legal_moves:
            board.push(move) # Add move to board
            score, _ = minimax(board, depth - 1, False, node_counter=node_counter) # Get potential score of move
            board.pop() # Remove move from board
            if score > best_score: # If move is better than current best, update best score and move
                best_score = score
                best_move = move
        return best_score, best_move
    else:
    # Minimizing branch
        best_score = float("inf") # Initialize to worst case for minimizing player.
        for move in legal_moves:
            board.push(move) # Add move to board
            score, _ = minimax(board, depth - 1, True, node_counter=node_counter) # Get potential score of move
            board.pop() # Remove move from board
            if score < best_score: # If move is better than current best, update best score and move
                best_score = score
                best_move = move
        return best_score, best_move


def choose_move(
    board: chess.Board,
    *,
    time_limit: Optional[float] = None,
    depth: Optional[int] = None,
) -> SearchResult:
    """
    Top-level Week 2 move chooser using depth-limited minimax.

    time_limit is currently unused (iterative deepening arrives in Week 5).
    depth defaults to DEFAULT_DEPTH when not supplied.
    """
    del time_limit
    search_depth = depth if depth is not None else DEFAULT_DEPTH

    # node_counter is a single-item list so recursive calls can mutate it.
    node_counter = [0]
    maximizing = board.turn == chess.WHITE
    best_score, best_move = minimax(board, search_depth, maximizing, node_counter=node_counter)
    return SearchResult(
        move=best_move,
        score=best_score,
        nodes=node_counter[0],
        depth=search_depth,
    )

