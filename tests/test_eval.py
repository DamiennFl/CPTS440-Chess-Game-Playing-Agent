import chess

from src import eval


def test_material_white_up_pawn() -> None:
    board = chess.Board("8/8/8/8/8/8/8/KP5k w - - 0 1")
    assert eval.evaluate(board) == 100.0


def test_material_black_up_pawn() -> None:
    board = chess.Board("8/8/8/8/8/8/8/kp5K b - - 0 1")
    assert eval.evaluate(board) == -100.0


def test_material_queen_vs_rook() -> None:
    # White has a queen, Black has a rook.
    board = chess.Board("7k/7r/8/8/8/8/8/KQ6 w - - 0 1")
    assert eval.evaluate(board) == 400.0


def test_insufficient_material_zero_score() -> None:
    board = chess.Board("8/8/8/8/8/8/8/K6k w - - 0 1")
    assert board.is_insufficient_material()
    assert eval.evaluate(board) == 0.0


def test_start_position_material_is_balanced() -> None:
    board = chess.Board()
    assert eval.evaluate(board) == 0.0


def test_promoted_extra_queen_swings_score() -> None:
    # White has promoted a pawn to gain an extra queen; Black only has king.
    board = chess.Board("7k/8/8/8/8/8/8/KQ6 w - - 0 1")
    # White queen (900) + White king (0) vs Black king (0) => +900.
    assert eval.evaluate(board) == 900.0


def test_multiple_queens_vs_rook_material_gap() -> None:
    # White: two queens. Black: one rook.
    board = chess.Board("7k/7r/8/8/8/8/8/KQQ5 w - - 0 1")
    # 2*900 - 500 = +1300
    assert eval.evaluate(board) == 1300.0


def test_invalid_fen_raises_value_error() -> None:
    try:
        chess.Board("not-a-fen")
    except ValueError:
        return
    raise AssertionError("Expected ValueError for invalid FEN")
