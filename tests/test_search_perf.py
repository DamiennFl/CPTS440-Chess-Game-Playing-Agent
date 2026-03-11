import time

import chess

from src import search


def test_minimax_depth_two_finishes_quickly() -> None:
    board = chess.Board()
    start = time.perf_counter()
    move = search.choose_move(board, depth=2)
    elapsed = time.perf_counter() - start

    # Depth 2 at the start position is ~400 nodes; should be comfortably fast.
    assert move is not None
    assert elapsed < 0.5  # seconds


def test_minimax_handles_terminal_quickly() -> None:
    # Stalemate position: no legal moves.
    board = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    start = time.perf_counter()
    move = search.choose_move(board, depth=3)
    elapsed = time.perf_counter() - start

    assert move is None  # No legal moves available.
    assert elapsed < 0.1