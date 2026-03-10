from __future__ import annotations

import chess

# Simple material values in centipawns.
# These mirror common classical values and keep kings at 0 because their
# intrinsic value is captured by terminal scoring.
PIECE_VALUES: dict[int, int] = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}


def evaluate(board: chess.Board) -> float:
    """
    Return a heuristic score from White's perspective.

    TO BE UPDATED LATER:
    - Terminal positions return large-magnitude scores.
    - Non-terminal positions use material balance (sum of piece values: White - Black).
    """
    if board.is_checkmate(): # Checkmate is a terminal position with a large score from the perspective of the winning side.
        return -1_000_000.0 if board.turn == chess.WHITE else 1_000_000.0
    if board.is_stalemate() or board.is_insufficient_material(): # Stalemate and insufficient material are terminal positions with a score of 0 (draw).
        return 0.0

    material = 0
    for square, piece in board.piece_map().items(): # Iterate over all pieces on the board and calculate material balance.
        value = PIECE_VALUES[piece.piece_type] # Get the value of the piece based on its type.
        material += value if piece.color == chess.WHITE else -value # Add value for White pieces, subtract for Black pieces.

    return float(material) # Return material balance as a float score from White's perspective.