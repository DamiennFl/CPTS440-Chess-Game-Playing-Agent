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
