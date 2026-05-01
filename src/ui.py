from __future__ import annotations

import argparse
import sys

import chess

from src.board import apply_move, from_fen, generate_legal_moves, has_move, moves_to_uci
from src.engine import play_human_vs_ai

START_FEN = chess.STARTING_FEN


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chess CLI — board inspection or human-vs-AI play.")
    parser.add_argument("--fen", default=START_FEN, help="FEN string to load (defaults to start position).")
    parser.add_argument(
        "--mode",
        choices=["inspect", "human"],
        default="inspect",
        help="'inspect' shows the board and legal moves; 'human' starts an interactive game against the AI.",
    )
    # inspect-mode options
    parser.add_argument(
        "--apply",
        default=None,
        help="(inspect mode) Optional UCI move to apply (e.g., e2e4 or a7a8q for promotion).",
    )
    # human-mode options
    parser.add_argument(
        "--color",
        choices=["white", "black"],
        default="white",
        help="(human mode) The side you want to play as.",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=2,
        help="(human mode) AI search depth in plies.",
    )
    parser.add_argument(
        "--max-moves",
        type=int,
        default=150,
        dest="max_moves",
        help="(human mode) Maximum full moves before the game is stopped.",
    )
    return parser.parse_args()


def _run_inspect(args: argparse.Namespace) -> int:
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


def _run_human(args: argparse.Namespace) -> int:
    human_color = chess.WHITE if args.color == "white" else chess.BLACK

    print(f"Starting human-vs-AI game.  You play {'White' if human_color == chess.WHITE else 'Black'}.")
    print("Type a UCI move (e.g. e2e4) and press Enter.  Type 'resign' to quit.\n")

    record = play_human_vs_ai(
        human_color=human_color,
        ai_depth=args.depth,
        max_moves=args.max_moves,
        fen=args.fen,
    )

    print(f"\nGame over — result: {record.result}")
    print(f"Total plies recorded: {len(record.plies)}")
    return 0


def main() -> int:
    args = parse_args()
    if args.mode == "human":
        return _run_human(args)
    return _run_inspect(args)


if __name__ == "__main__":
    raise SystemExit(main())

