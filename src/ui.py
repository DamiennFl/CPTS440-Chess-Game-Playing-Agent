from __future__ import annotations

import argparse
import sys

import chess

from src.board import apply_move, from_fen, generate_legal_moves, has_move, moves_to_uci

START_FEN = chess.STARTING_FEN


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Minimal chess CLI for Week 1 scaffolding.")
    parser.add_argument("--fen", default=START_FEN, help="FEN string to load (defaults to start position).")
    parser.add_argument(
        "--apply",
        default=None,
        help="Optional UCI move to apply (e.g., e2e4 or a7a8q for promotion).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        board = from_fen(args.fen)
    except ValueError as exc:
        print(f"Invalid FEN: {exc}", file=sys.stderr)
        return 2

    print("Loaded FEN:")
    print(board.fen())
    print(f"Side to move: {'White' if board.turn == chess.WHITE else 'Black'}")

    legal_moves = generate_legal_moves(board)
    legal_uci = moves_to_uci(legal_moves)
    print(f"Legal move count: {len(legal_uci)}")
    print("Legal moves:", " ".join(legal_uci))

    if args.apply is not None:
        if not has_move(board, args.apply):
            print(f"Illegal or invalid move in this position: {args.apply}", file=sys.stderr)
            return 3
        next_board = apply_move(board, chess.Move.from_uci(args.apply))
        print("Applied move:", args.apply)
        print("Resulting FEN:")
        print(next_board.fen())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

