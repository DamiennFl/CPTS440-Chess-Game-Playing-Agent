"""
Comparative tests for evaluate() with use_pst=True vs use_pst=False.

These tests document the behavioural *difference* the PST layer introduces
so regressions are immediately visible if the tables or toggle are changed.

Fixtures
--------
Two positions are used throughout:
  FEN_KNIGHT_CENTER — White knight on e4  (PST_KNIGHT[28] = +20 cp)
  FEN_KNIGHT_RIM    — White knight on a1  (PST_KNIGHT[0]  = -50 cp)
Both positions include an identical White pawn on h2 and kings on e1/e8 that
cancel exactly in the PST (king PST[4] == 0, mirrored square also 4 == 0).
The pawn-on-h2 prevents K+N vs K from being flagged as insufficient material.
"""

import chess

from src import eval

# White: King e1, Knight e4 (center), Pawn h2.  Black: King e8.
FEN_KNIGHT_CENTER = "4k3/8/8/8/4N3/8/7P/4K3 w - - 0 1"

# White: King e1, Knight a1 (rim),    Pawn h2.  Black: King e8.
FEN_KNIGHT_RIM = "4k3/8/8/8/8/8/7P/N3K3 w - - 0 1"


def test_pst_off_knight_placement_irrelevant() -> None:
    """Without PSTs (or any positional terms) both positions are worth the same material."""
    center = chess.Board(FEN_KNIGHT_CENTER)
    rim = chess.Board(FEN_KNIGHT_RIM)
    kwargs = dict(use_pst=False, use_pawn_structure=False, use_mobility=False, use_king_safety=False)
    assert eval.evaluate(center, **kwargs) == eval.evaluate(rim, **kwargs)


def test_pst_on_knight_center_scores_higher() -> None:
    """PSTs (plus other positional terms) make the centralized knight score higher."""
    center = chess.Board(FEN_KNIGHT_CENTER)
    rim = chess.Board(FEN_KNIGHT_RIM)
    assert eval.evaluate(center, use_pst=True) > eval.evaluate(rim, use_pst=True)


def test_pst_off_equals_material_sum() -> None:
    """With all positional terms off, score equals raw material balance."""
    # White: King + Queen (900 cp).  Black: King (0 cp).  Net = 900.
    board = chess.Board("7k/8/8/8/8/8/8/KQ6 w - - 0 1")
    assert eval.evaluate(board, use_pst=False, use_pawn_structure=False, use_mobility=False, use_king_safety=False) == 900.0


def test_start_position_both_modes_zero() -> None:
    """Starting position evaluates to 0 in both modes (material and PST symmetry)."""
    board = chess.Board()
    assert eval.evaluate(board, use_pst=True) == 0.0
    assert eval.evaluate(board, use_pst=False) == 0.0
