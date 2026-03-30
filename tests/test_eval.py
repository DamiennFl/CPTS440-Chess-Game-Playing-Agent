import chess

from src import eval


def test_material_white_up_pawn() -> None:
    # Material: +100 (pawn). PST: White king a1 +20, Black king h1 adds +30 from White's perspective.
    board = chess.Board("8/8/8/8/8/8/8/KP5k w - - 0 1")
    assert eval.evaluate(board) == 150.0


def test_material_black_up_pawn() -> None:
    # Material: -100 (pawn). PST: Black king a1 adds +30, White king h1 adds +20 from White's perspective.
    board = chess.Board("8/8/8/8/8/8/8/kp5K b - - 0 1")
    assert eval.evaluate(board) == -50.0


def test_material_queen_vs_rook() -> None:
    # Material: +400 (900 queen - 500 rook). PST offsets net -5 from piece and king positions.
    board = chess.Board("7k/7r/8/8/8/8/8/KQ6 w - - 0 1")
    assert eval.evaluate(board) == 395.0


def test_insufficient_material_zero_score() -> None:
    board = chess.Board("8/8/8/8/8/8/8/K6k w - - 0 1")
    assert board.is_insufficient_material()
    assert eval.evaluate(board) == 0.0


def test_start_position_material_is_balanced() -> None:
    board = chess.Board()
    assert eval.evaluate(board) == 0.0


def test_promoted_extra_queen_swings_score() -> None:
    # White has an extra queen; Black only has a king.
    # Material: +900. PST offsets net -10 from queen and king positions.
    board = chess.Board("7k/8/8/8/8/8/8/KQ6 w - - 0 1")
    assert eval.evaluate(board) == 890.0


def test_multiple_queens_vs_rook_material_gap() -> None:
    # White: two queens. Black: one rook.
    # Material: 2*900 - 500 = +1300. PST offsets net -15 from queen and king positions.
    board = chess.Board("7k/7r/8/8/8/8/8/KQQ5 w - - 0 1")
    assert eval.evaluate(board) == 1285.0


def test_invalid_fen_raises_value_error() -> None:
    try:
        chess.Board("not-a-fen")
    except ValueError:
        return
    raise AssertionError("Expected ValueError for invalid FEN")


def test_pst_knight_center_better_than_rim() -> None:
    # Knight on e4 (PST=+20) vs a1 (PST=-50). A White pawn on h2 is present in
    # both positions (same square, same PST) so it contributes equally and the
    # score difference reflects only the knight's positional bonus.
    # K+N+P vs K is sufficient material, avoiding the draw early-exit in evaluate().
    center = chess.Board("4k3/8/8/8/4N3/8/7P/4K3 w - - 0 1")
    rim = chess.Board("4k3/8/8/8/8/8/7P/N3K3 w - - 0 1")
    assert eval.evaluate(center) == 445.0   # (320+20) + (100+5)
    assert eval.evaluate(rim) == 375.0      # (320-50) + (100+5)
    assert eval.evaluate(center) > eval.evaluate(rim)


def test_pst_pawn_advances_to_center() -> None:
    # Pawn on e4 (PST=+20) rewarded more than pawn on e2 (PST=-20). Kings cancel.
    advanced = chess.Board("4k3/8/8/8/4P3/8/8/4K3 w - - 0 1")
    starting = chess.Board("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1")
    assert eval.evaluate(advanced) == 120.0  # 100 + 20
    assert eval.evaluate(starting) == 80.0   # 100 - 20
    assert eval.evaluate(advanced) > eval.evaluate(starting)


def test_pst_king_castled_better_than_center() -> None:
    # White king g1 (PST=+30) beats e1 (PST=0) against the same Black king.
    # A White pawn on h2 is present in both to avoid K vs K insufficient material.
    # The pawn (100+5=105) cancels between positions; score difference = 30 cp.
    castled = chess.Board("4k3/8/8/8/8/8/7P/6K1 w - - 0 1")
    center = chess.Board("4k3/8/8/8/8/8/7P/4K3 w - - 0 1")
    assert eval.evaluate(castled) == 135.0  # (0+30) + (100+5)
    assert eval.evaluate(center) == 105.0   # (0+0)  + (100+5)
    assert eval.evaluate(castled) > eval.evaluate(center)
