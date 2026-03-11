import tempfile
from pathlib import Path

import chess

from src.engine import GameRecord, PlayRecord, play_game
from src.viz import export_game_html


def test_play_game_from_terminal_fen_produces_empty_plies() -> None:
    # Starting from a stalemate position: no moves available, loop exits immediately.
    stalemate_fen = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
    record = play_game(depth=1, max_moves=10, fen=stalemate_fen)

    assert record.plies == []
    assert record.final_fen == stalemate_fen
    # Stalemate is a draw — result should not be a decisive outcome.
    assert record.result in {"1/2-1/2", "*"}


def test_play_game_one_full_move_produces_two_plies() -> None:
    record = play_game(depth=1, max_moves=1)

    # max_moves=1 means one full move, unless the game ends sooner.
    assert 1 <= len(record.plies) <= 2


def test_play_game_ply_fields_are_consistent() -> None:
    record = play_game(depth=1, max_moves=3)

    for ply in record.plies:
        # FEN must be parseable.
        chess.Board(ply.fen_before)
        # Move must be legal in that position.
        board = chess.Board(ply.fen_before)
        assert chess.Move.from_uci(ply.move_uci) in board.legal_moves
        # Node count must be positive (at least the root was visited).
        assert ply.nodes > 0


def test_play_game_final_fen_matches_plies_applied() -> None:
    record = play_game(depth=1, max_moves=4)

    # Replay all recorded moves from the start and verify we reach final_fen.
    board = chess.Board(record.plies[0].fen_before) if record.plies else chess.Board()
    for ply in record.plies:
        board.push(chess.Move.from_uci(ply.move_uci))

    assert board.fen() == record.final_fen


def test_export_game_html_creates_file() -> None:
    record = play_game(depth=1, max_moves=2)

    with tempfile.TemporaryDirectory() as tmp:
        out = export_game_html(record, Path(tmp) / "replay.html")
        assert out.exists()


def test_export_game_html_contains_expected_markers() -> None:
    record = play_game(depth=1, max_moves=2)

    with tempfile.TemporaryDirectory() as tmp:
        out = export_game_html(record, Path(tmp) / "replay.html")
        content = out.read_text(encoding="utf-8")

    # JS frames array must be present and non-empty.
    assert "const frames = [" in content
    # At least the start frame label.
    assert "Start" in content
    # Each ply must produce a labelled frame (move_uci should appear in a label).
    for ply in record.plies:
        assert ply.move_uci in content
    # Controls must be rendered.
    assert "btn-play" in content
    assert "btn-prev" in content
