from __future__ import annotations

from typing import Iterable

import chess


def from_fen(fen: str) -> chess.Board:
    """Create a board from a FEN string."""
    return chess.Board(fen=fen)


def to_fen(board: chess.Board) -> str:
    """Serialize a board to FEN."""
    return board.fen()


def generate_legal_moves(board: chess.Board) -> list[chess.Move]:
    """Return legal moves for the current side to move."""
    return list(board.legal_moves)


def apply_move(board: chess.Board, move: chess.Move) -> chess.Board:
    """
    Return a new board with move applied.
    The input board is left unchanged.
    """
    next_board = board.copy(stack=True)
    next_board.push(move)
    return next_board


def is_terminal(board: chess.Board) -> bool:
    """True if game is over by any standard chess termination."""
    return board.is_game_over()


def result(board: chess.Board) -> str:
    """Return game result string (e.g., '1-0', '0-1', '1/2-1/2', or '*')."""
    return board.result(claim_draw=True) if board.is_game_over(claim_draw=True) else "*"


def has_move(board: chess.Board, uci_move: str) -> bool:
    """Check if a UCI move string is legal in the position."""
    try:
        move = chess.Move.from_uci(uci_move)
    except ValueError:
        return False
    return move in board.legal_moves


def moves_to_uci(moves: Iterable[chess.Move]) -> list[str]:
    """Convert a move iterable to UCI strings."""
    return [m.uci() for m in moves]

