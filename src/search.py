from __future__ import annotations

import time
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
    # Week 5: wall-clock time for this move search, used by Week 6 experiments/reports.
    elapsed: float = 0.0


PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}

# Soft cap used for iterative deepening when no explicit max depth is provided.
MAX_ITERATIVE_DEPTH = 64


class SearchTimeout(Exception):
    """Raised internally to abort search when the time budget is exhausted."""


def _capture_target_piece(board: chess.Board, move: chess.Move) -> Optional[chess.Piece]:
    """Return captured piece for normal captures and en passant."""
    if not board.is_capture(move):
        return None

    target = board.piece_at(move.to_square)
    if target is not None:
        return target

    # En passant capture: the captured pawn is behind the destination square.
    direction = -8 if board.turn == chess.WHITE else 8
    return board.piece_at(move.to_square + direction)


def _move_priority(board: chess.Board, move: chess.Move) -> tuple[int, int, int, str]:
    """Score moves for deterministic ordering to increase alpha-beta cutoffs."""
    attacker = board.piece_at(move.from_square)
    attacker_value = PIECE_VALUES.get(attacker.piece_type, 0) if attacker else 0

    capture_score = 0
    captured_piece = _capture_target_piece(board, move)
    if captured_piece is not None:
        victim_value = PIECE_VALUES.get(captured_piece.piece_type, 0)
        # MVV-LVA style: favor high-value victim with low-value attacker.
        capture_score = 10_000 + victim_value * 10 - attacker_value

    check_bonus = 500 if board.gives_check(move) else 0
    promotion_bonus = PIECE_VALUES.get(move.promotion, 0) if move.promotion else 0
    return (capture_score, check_bonus, promotion_bonus, move.uci())


def order_moves(board: chess.Board) -> list[chess.Move]:
    """
    Deterministic move ordering to improve pruning.

    Priority favors captures (MVV-LVA style), checking moves, then promotions.
    """
    # Week 5: upgraded from basic capture/check sort to deterministic MVV-LVA style ordering.
    legal = list(board.legal_moves)
    legal.sort(key=lambda m: _move_priority(board, m), reverse=True)
    return legal


# Default search depth (plies). Adjust as needed or override via choose_move(..., depth=...).
DEFAULT_DEPTH = 2


def minimax(
    board: chess.Board,
    depth: int,
    maximizing_player: bool,
    *,
    node_counter: Optional[list[int]] = None,
    deadline: Optional[float] = None,
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
    if deadline is not None and time.perf_counter() >= deadline:
        raise SearchTimeout

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
            try:
                score, _ = minimax(
                    board,
                    depth - 1,
                    False,
                    node_counter=node_counter,
                    deadline=deadline,
                ) # Get potential score of move
            finally:
                # Always unwind board state even when SearchTimeout bubbles up.
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
            try:
                score, _ = minimax(
                    board,
                    depth - 1,
                    True,
                    node_counter=node_counter,
                    deadline=deadline,
                ) # Get potential score of move
            finally:
                # Always unwind board state even when SearchTimeout bubbles up.
                board.pop() # Remove move from board
            if score < best_score: # If move is better than current best, update best score and move
                best_score = score
                best_move = move
        return best_score, best_move


def alphabeta(
    board: chess.Board,
    depth: int,
    maximizing_player: bool,
    *,
    alpha: float = float("-inf"),
    beta: float = float("inf"),
    node_counter: Optional[list[int]] = None,
    deadline: Optional[float] = None,
) -> Tuple[float, Optional[chess.Move]]:
    """
    Depth-limited minimax search with alpha-beta pruning.

    Args:
        board: current chess position (mutated via push/pop during search).
        depth: remaining plies to explore (0 == evaluate current node).
        maximizing_player: True if the side to move is treated as the maximizing player.
        alpha: best score the maximizing player can guarantee so far.
        beta: best score the minimizing player can guarantee so far.
        node_counter: optional single-element list used to count visited nodes for debugging/metrics.

    Returns:
        (score, best_move) where score is from White's perspective.
        best_move is None for leaf/terminal nodes.
    """
    # Time control hook used by iterative deepening. Raising here lets callers
    # stop the current deep search and keep the last completed depth result.
    if deadline is not None and time.perf_counter() >= deadline:
        raise SearchTimeout

    if node_counter is not None:
        node_counter[0] += 1

    # Leaf node (depth exhausted) or terminal game state.
    if depth == 0 or board.is_game_over():
        return eval.evaluate(board), None

    legal_moves = order_moves(board)
    if not legal_moves:
        return eval.evaluate(board), None

    best_move = None
    if maximizing_player:
        # Maximizing side seeks the highest score and raises alpha.
        best_score = float("-inf")
        for move in legal_moves:
            board.push(move)
            try:
                score, _ = alphabeta(
                    board,
                    depth - 1,
                    False,
                    alpha=alpha,
                    beta=beta,
                    node_counter=node_counter,
                    deadline=deadline,
                )
            finally:
                # Always unwind board state even when SearchTimeout bubbles up.
                board.pop()
            if score > best_score:
                best_score = score
                best_move = move
            # Alpha tracks the best guaranteed score for the maximizing side.
            alpha = max(alpha, best_score)
            # Cutoff: minimizing parent already has a better or equal option.
            if alpha >= beta:
                break
        return best_score, best_move

    # Minimizing side seeks the lowest score and lowers beta.
    best_score = float("inf")
    for move in legal_moves:
        board.push(move)
        try:
            score, _ = alphabeta(
                board,
                depth - 1,
                True,
                alpha=alpha,
                beta=beta,
                node_counter=node_counter,
                deadline=deadline,
            )
        finally:
            # Always unwind board state even when SearchTimeout bubbles up.
            board.pop()
        if score < best_score:
            best_score = score
            best_move = move
        # Beta tracks the best guaranteed score for the minimizing side.
        beta = min(beta, best_score)
        # Cutoff: maximizing parent already has a better or equal option.
        if alpha >= beta:
            break
    return best_score, best_move


def choose_move(
    board: chess.Board,
    *,
    time_limit: Optional[float] = None,
    depth: Optional[int] = None,
    use_alpha_beta: bool = True,
) -> SearchResult:
    """
    Top-level move chooser using minimax/alpha-beta search.

    When time_limit is provided, iterative deepening is used and the best
    completed iteration is returned.

    depth defaults to DEFAULT_DEPTH for fixed-depth search, and acts as an
    upper bound for iterative deepening when both depth and time_limit are set.
    use_alpha_beta keeps plain minimax available for debugging and measurement.
    """
    start_time = time.perf_counter()
    maximizing = board.turn == chess.WHITE
    search_fn = alphabeta if use_alpha_beta else minimax

    # No time budget: keep fixed-depth behavior for deterministic evaluation/testing.
    if time_limit is None:
        search_depth = depth if depth is not None else DEFAULT_DEPTH
        # node_counter is a single-item list so recursive calls can mutate it.
        node_counter = [0]
        best_score, best_move = search_fn(board, search_depth, maximizing, node_counter=node_counter)
        return SearchResult(
            move=best_move,
            score=best_score,
            nodes=node_counter[0],
            depth=search_depth,
            elapsed=time.perf_counter() - start_time,
        )

    # Week 5: iterative deepening for time-limited search. We return the deepest
    # fully completed iteration rather than a partially searched tree.
    budget = max(0.0, time_limit)
    deadline = time.perf_counter() + budget
    max_depth = depth if depth is not None else MAX_ITERATIVE_DEPTH
    total_nodes = 0
    best_completed: Optional[SearchResult] = None

    for current_depth in range(1, max_depth + 1):
        if time.perf_counter() >= deadline:
            break

        node_counter = [0]
        try:
            best_score, best_move = search_fn(
                board,
                current_depth,
                maximizing,
                node_counter=node_counter,
                deadline=deadline,
            )
        except SearchTimeout:
            break

        total_nodes += node_counter[0]
        best_completed = SearchResult(
            move=best_move,
            score=best_score,
            nodes=node_counter[0],
            depth=current_depth,
        )

    if best_completed is not None:
        return SearchResult(
            move=best_completed.move,
            score=best_completed.score,
            nodes=total_nodes,
            depth=best_completed.depth,
            elapsed=time.perf_counter() - start_time,
        )

    # If budget is exhausted before any depth completes, return a deterministic fallback.
    # This guarantees a legal move is still produced when possible.
    legal_moves = order_moves(board)
    fallback_move = legal_moves[0] if legal_moves else None
    return SearchResult(
        move=fallback_move,
        score=eval.evaluate(board),
        nodes=0,
        depth=0,
        elapsed=time.perf_counter() - start_time,
    )
