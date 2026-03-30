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

# ---------------------------------------------------------------------------
# Piece-square tables (PSTs) — positional bonuses in centipawns.
#
# Each table is 64 values indexed by square (a1=0 … h8=63), read rank by rank
# from rank 1 (White's back rank) up to rank 8.  All values are from White's
# perspective; for Black, the table is mirrored vertically via `square ^ 56`.
#
# Source: Simplified Evaluation Function (chessprogramming.org/Simplified_Evaluation_Function)
# These are standard tuning constants and is not original creative work.
# ---------------------------------------------------------------------------

# fmt: off
PST_PAWN: list[int] = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10,-20,-20, 10, 10,  5,
     5, -5,-10,  0,  0,-10, -5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5,  5, 10, 25, 25, 10,  5,  5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
     0,  0,  0,  0,  0,  0,  0,  0,
]

PST_KNIGHT: list[int] = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

PST_BISHOP: list[int] = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

PST_ROOK: list[int] = [
     0,  0,  0,  5,  5,  0,  0,  0,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     5, 10, 10, 10, 10, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]

PST_QUEEN: list[int] = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -10,  5,  5,  5,  5,  5,  0,-10,
      0,  0,  5,  5,  5,  5,  0, -5,
     -5,  0,  5,  5,  5,  5,  0, -5,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]

PST_KING_MIDDLEGAME: list[int] = [
     20, 30, 10,  0,  0, 10, 30, 20,
     20, 20,  0,  0,  0,  0, 20, 20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
]

# Map each piece type to its PST.
PST: dict[int, list[int]] = {
    chess.PAWN:   PST_PAWN,
    chess.KNIGHT: PST_KNIGHT,
    chess.BISHOP: PST_BISHOP,
    chess.ROOK:   PST_ROOK,
    chess.QUEEN:  PST_QUEEN,
    chess.KING:   PST_KING_MIDDLEGAME,
}


def evaluate(board: chess.Board, *, use_pst: bool = True) -> float:
    """
    Return a heuristic score from White's perspective.

    Terminal positions return large-magnitude scores (checkmate) or 0 (draw).
    Non-terminal positions combine material balance with piece-square table
    bonuses: each piece's value is its material worth plus a positional bonus
    that rewards good squares (center control, king safety, piece activity).
    Black's PST values are mirrored vertically via `square ^ 56`.

    Args:
        board: position to evaluate.
        use_pst: if False, only material values are used (no positional bonus).
    """
    if board.is_checkmate():
        return -1_000_000.0 if board.turn == chess.WHITE else 1_000_000.0
    if board.is_stalemate() or board.is_insufficient_material():
        return 0.0

    score = 0
    for square, piece in board.piece_map().items():
        material = PIECE_VALUES[piece.piece_type]
        if use_pst:
            pst_square = square if piece.color == chess.WHITE else square ^ 56
            positional = PST[piece.piece_type][pst_square]
        else:
            positional = 0
        value = material + positional
        score += value if piece.color == chess.WHITE else -value

    return float(score)