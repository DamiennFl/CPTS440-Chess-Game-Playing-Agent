from pathlib import Path

import chess


def test_fen_fixture_count_and_validity() -> None:
    fixture_path = Path("tests/fixtures/fen_positions.txt")
    raw_lines = fixture_path.read_text(encoding="utf-8").splitlines()
    fens = [line.strip() for line in raw_lines if line.strip() and not line.strip().startswith("#")]

    assert len(fens) >= 5

    for fen in fens:
        board = chess.Board(fen=fen)
        assert board.is_valid()

