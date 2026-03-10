import chess

from src.board import (
    apply_move,
    from_fen,
    generate_legal_moves,
    has_move,
    is_terminal,
    moves_to_uci,
    result,
    to_fen,
)


def test_round_trip_fen_and_non_mutating_apply() -> None:
    board = from_fen(chess.STARTING_FEN)
    assert to_fen(board) == chess.STARTING_FEN

    moved = apply_move(board, chess.Move.from_uci("e2e4"))
    assert moved.fen() != board.fen()
    assert board.fen() == chess.STARTING_FEN


def test_checkmate_and_stalemate_detection() -> None:
    checkmate_fen = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
    stalemate_fen = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"

    mate_board = from_fen(checkmate_fen)
    assert is_terminal(mate_board)
    assert result(mate_board) == "0-1"

    stale_board = from_fen(stalemate_fen)
    assert is_terminal(stale_board)
    assert result(stale_board) == "1/2-1/2"


def test_threefold_repetition_claim() -> None:
    board = chess.Board()
    sequence = ["g1f3", "g8f6", "f3g1", "f6g8"] * 2
    for uci in sequence:
        board.push(chess.Move.from_uci(uci))
    assert board.can_claim_threefold_repetition()


def test_fifty_move_claim() -> None:
    board = from_fen("8/8/8/8/8/8/8/K6k w - - 100 1")
    assert board.can_claim_fifty_moves()


def test_castling_and_promotion_legality_helpers() -> None:
    castling_board = from_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    castling_moves = moves_to_uci(generate_legal_moves(castling_board))
    assert "e1g1" in castling_moves
    assert "e1c1" in castling_moves

    promotion_board = from_fen("7k/P7/8/8/8/8/8/K7 w - - 0 1")
    assert has_move(promotion_board, "a7a8q")
    assert has_move(promotion_board, "a7a8r")
    assert has_move(promotion_board, "a7a8b")
    assert has_move(promotion_board, "a7a8n")

