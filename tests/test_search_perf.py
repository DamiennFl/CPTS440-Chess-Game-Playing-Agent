import sys
import time
from pathlib import Path

import chess

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import search


def test_minimax_depth_two_finishes_quickly() -> None:
    board = chess.Board()
    start = time.perf_counter()
    result = search.choose_move(board, depth=2)
    elapsed = time.perf_counter() - start

    # Depth 2 at the start position is ~400 nodes; should be comfortably fast.
    assert result.move is not None
    assert result.nodes > 0
    assert result.depth == 2
    assert elapsed < 0.5  # seconds


def test_minimax_handles_terminal_quickly() -> None:
    # Stalemate position: no legal moves.
    board = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    start = time.perf_counter()
    result = search.choose_move(board, depth=3)
    elapsed = time.perf_counter() - start

    assert result.move is None  # No legal moves available.
    assert result.score == 0.0  # Stalemate is a draw.
    assert elapsed < 0.1


def test_alpha_beta_matches_minimax_score() -> None:
    board = chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 2 3")

    minimax_result = search.choose_move(board.copy(stack=False), depth=3, use_alpha_beta=False)
    alpha_beta_result = search.choose_move(board.copy(stack=False), depth=3, use_alpha_beta=True)

    assert minimax_result.move is not None
    assert alpha_beta_result.move is not None
    assert minimax_result.score == alpha_beta_result.score


def test_alpha_beta_reduces_node_expansion() -> None:
    board = chess.Board("r1bqk1nr/pppp1ppp/2n5/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4")

    minimax_result = search.choose_move(board.copy(stack=False), depth=3, use_alpha_beta=False)
    alpha_beta_result = search.choose_move(board.copy(stack=False), depth=3, use_alpha_beta=True)

    assert alpha_beta_result.move is not None
    assert minimax_result.nodes > alpha_beta_result.nodes


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__]))
