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
# These are standard tuning constants and are not original creative work.
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

# King endgame PST — rewards an active, centralised king.
# Values are from White's perspective; Black mirrors via `square ^ 56`.
# Source: Simplified Evaluation Function (chessprogramming.org/Simplified_Evaluation_Function)
PST_KING_ENDGAME: list[int] = [
    -50,-30,-30,-30,-30,-30,-30,-50,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -50,-40,-30,-20,-20,-30,-40,-50,
]
# fmt: on

# Map each piece type to its PST.
PST: dict[int, list[int]] = {
    chess.PAWN:   PST_PAWN,
    chess.KNIGHT: PST_KNIGHT,
    chess.BISHOP: PST_BISHOP,
    chess.ROOK:   PST_ROOK,
    chess.QUEEN:  PST_QUEEN,
    chess.KING:   PST_KING_MIDDLEGAME,
}

# Total non-pawn, non-king material threshold below which we consider it an endgame.
# Roughly: each side having at most one rook + one minor piece left (~1300 cp combined).
_ENDGAME_MATERIAL_THRESHOLD = 1300


def _is_endgame(board: chess.Board) -> bool:
    """
    Return True when the position is an endgame.

    Calculated as the sum of non-pawn, non-king material for *both* sides
    combined.  When that total falls at or below _ENDGAME_MATERIAL_THRESHOLD
    (≈ rook + minor piece per side) the king should become active.
    """
    total = 0
    for piece in board.piece_map().values():
        if piece.piece_type not in (chess.PAWN, chess.KING):
            total += PIECE_VALUES[piece.piece_type]
    return total <= _ENDGAME_MATERIAL_THRESHOLD


# Pawn structure penalty/bonus constants (centipawns).
_DOUBLED_PAWN_PENALTY  = -20   # per extra pawn beyond the first on a file
_ISOLATED_PAWN_PENALTY = -15   # per pawn with no friendly pawn on adjacent files
_PASSED_PAWN_BONUS     =  20   # per pawn with no enemy pawns blocking or attacking ahead


def _pawn_structure_score(board: chess.Board, color: chess.Color) -> int:
    """
    Return a pawn-structure score (in centipawns) for *one* side.

    Three terms are evaluated in a single pass over the pawn bitboard:

    * **Doubled pawns:** more than one friendly pawn on the same file.
      Each extra pawn beyond the first incurs _DOUBLED_PAWN_PENALTY.
    * **Isolated pawns:** a pawn with no friendly pawn on either adjacent
      file.  Each such pawn incurs _ISOLATED_PAWN_PENALTY.
    * **Passed pawns:** a pawn that has no enemy pawn on the same file or
      either adjacent file *ahead* of it (from the moving side's perspective).
      Each such pawn earns _PASSED_PAWN_BONUS.

    The score is always from the perspective of `color` (positive = good for
    that side).  The caller is responsible for negating when needed.
    """
    enemy = not color

    friendly_pawns: dict[int, list[int]] = {}  # file -> list of ranks
    enemy_pawn_files: set[int] = set()

    for square, piece in board.piece_map().items():
        if piece.piece_type != chess.PAWN:
            continue
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        if piece.color == color:
            friendly_pawns.setdefault(file, []).append(rank)
        else:
            enemy_pawn_files.add(file)

    score = 0
    for file, ranks in friendly_pawns.items():
        # Doubled pawn penalty
        if len(ranks) > 1:
            score += (len(ranks) - 1) * _DOUBLED_PAWN_PENALTY

        # Isolated pawn penalty (per pawn on this file)
        has_neighbor = (file - 1) in friendly_pawns or (file + 1) in friendly_pawns
        if not has_neighbor:
            score += len(ranks) * _ISOLATED_PAWN_PENALTY

        # Passed pawn bonus (per pawn on this file)
        # Enemy pawns on the same or adjacent files that are "ahead" would block.
        blocking_files = {file - 1, file, file + 1} & enemy_pawn_files
        for rank in ranks:
            # Ahead means higher ranks for White, lower ranks for Black.
            if color == chess.WHITE:
                enemy_ahead = any(
                    chess.square_rank(sq) > rank
                    for sq, pc in board.piece_map().items()
                    if pc.piece_type == chess.PAWN
                    and pc.color == enemy
                    and chess.square_file(sq) in blocking_files
                )
            else:
                enemy_ahead = any(
                    chess.square_rank(sq) < rank
                    for sq, pc in board.piece_map().items()
                    if pc.piece_type == chess.PAWN
                    and pc.color == enemy
                    and chess.square_file(sq) in blocking_files
                )
            if not enemy_ahead:
                score += _PASSED_PAWN_BONUS

    return score


# Mobility bonus per legal move (centipawns).
_MOBILITY_BONUS_PER_MOVE = 4


def _mobility_score(board: chess.Board) -> int:
    """
    Return a mobility score from White's perspective (centipawns).

    Counts the number of legal moves available to each side and returns
    (white_moves - black_moves) * _MOBILITY_BONUS_PER_MOVE.

    To count the opponent's moves we temporarily flip the turn.  This is
    safe because we never push a move and we only read legal_moves.
    """
    # Moves for the side currently to move.
    if board.turn == chess.WHITE:
        white_moves = board.legal_moves.count()
        board.turn = chess.BLACK
        black_moves = board.legal_moves.count()
        board.turn = chess.WHITE
    else:
        black_moves = board.legal_moves.count()
        board.turn = chess.WHITE
        white_moves = board.legal_moves.count()
        board.turn = chess.BLACK

    return (white_moves - black_moves) * _MOBILITY_BONUS_PER_MOVE


# King safety penalty constants (centipawns).
_OPEN_FILE_KING_PENALTY      = -25   # no pawns at all on the king's file
_HALF_OPEN_FILE_KING_PENALTY = -10   # only enemy pawns on the king's file (semi-open)


def _king_safety_score(board: chess.Board, color: chess.Color) -> int:
    """
    Return a king-safety score (centipawns) for *one* side.

    Scans the three files around the king (king file ± 1, clamped to a–h)
    and penalises each file that lacks a friendly pawn shield:

    * Open file: no pawns of either colour → _OPEN_FILE_KING_PENALTY
    * Half-open file: only enemy pawns present → _HALF_OPEN_FILE_KING_PENALTY

    Files that have at least one friendly pawn are fine and score 0.
    The score is from the perspective of `color` (negative = bad for that side).
    """
    king_square = board.king(color)
    if king_square is None:
        return 0  # shouldn't happen in a legal position

    king_file = chess.square_file(king_square)
    score = 0

    for f in range(max(0, king_file - 1), min(7, king_file + 1) + 1):
        friendly_on_file = any(
            pc.piece_type == chess.PAWN and pc.color == color
            for sq, pc in board.piece_map().items()
            if chess.square_file(sq) == f
        )
        enemy_on_file = any(
            pc.piece_type == chess.PAWN and pc.color != color
            for sq, pc in board.piece_map().items()
            if chess.square_file(sq) == f
        )

        if not friendly_on_file and not enemy_on_file:
            score += _OPEN_FILE_KING_PENALTY
        elif not friendly_on_file and enemy_on_file:
            score += _HALF_OPEN_FILE_KING_PENALTY

    return score


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