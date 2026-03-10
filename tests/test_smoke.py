import chess


def test_python_chess_smoke_flow() -> None:
    board = chess.Board()
    assert board.fen() == chess.STARTING_FEN
    assert board.legal_moves.count() == 20

    move = chess.Move.from_uci("e2e4")
    assert move in board.legal_moves

    board.push(move)
    assert board.fullmove_number == 1
    assert board.turn == chess.BLACK

    board.pop()
    assert board.fen() == chess.STARTING_FEN

