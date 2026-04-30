from __future__ import annotations

import builtins
from dataclasses import dataclass, field
from typing import Callable, Optional

import chess

from src.search import SearchResult, choose_move as search_choose_move


def choose_move(
    board: chess.Board,
    *,
    time_limit: Optional[float] = None,
    depth: Optional[int] = None,
    use_alpha_beta: bool = True,
) -> SearchResult:
    """Top-level engine hook for move selection."""
    # Week 5/6 passthrough: preserve search configuration for experiments
    # (fixed depth vs time-limited iterative deepening, and AB vs minimax).
    return search_choose_move(
        board,
        time_limit=time_limit,
        depth=depth,
        use_alpha_beta=use_alpha_beta,
    )


@dataclass
class PlayRecord:
    """Snapshot of a single half-move in a game."""

    fen_before: str
    move_uci: str
    score: float
    nodes: int
    # Week 6 telemetry: per-move search time and depth for experiment and replay reporting.
    elapsed: float = 0.0
    depth: int = 0


@dataclass
class GameRecord:
    """Complete record of an AI-vs-AI game."""

    plies: list[PlayRecord] = field(default_factory=list)
    final_fen: str = chess.STARTING_FEN
    result: str = "*"

    # ------------------------------------------------------------------
    # Aggregate telemetry computed from plies, read-only.
    # Human-move plies have elapsed=0 and depth=0 and are excluded from
    # AI-only aggregates (avg_depth) but included in timing totals.
    # ------------------------------------------------------------------

    @property
    def total_time_ms(self) -> float:
        """Total wall-clock time across all plies, in milliseconds."""
        return sum(p.elapsed for p in self.plies) * 1000.0

    @property
    def avg_time_ms(self) -> float:
        """Average wall-clock time per ply, in milliseconds. 0.0 if no plies."""
        if not self.plies:
            return 0.0
        return self.total_time_ms / len(self.plies)

    @property
    def avg_nodes(self) -> float:
        """Average nodes searched per ply. 0.0 if no plies."""
        if not self.plies:
            return 0.0
        return sum(p.nodes for p in self.plies) / len(self.plies)

    @property
    def peak_nodes(self) -> int:
        """Maximum nodes searched in a single ply. 0 if no plies."""
        if not self.plies:
            return 0
        return max(p.nodes for p in self.plies)

    @property
    def avg_depth(self) -> float:
        """Average search depth across AI plies (depth > 0). 0.0 if none."""
        ai_plies = [p for p in self.plies if p.depth > 0]
        if not ai_plies:
            return 0.0
        return sum(p.depth for p in ai_plies) / len(ai_plies)


def play_game(
    *,
    white_depth: int = 2,
    black_depth: int = 2,
    time_limit: Optional[float] = None,
    use_alpha_beta: bool = True,
    max_moves: int = 150,
    fen: str = chess.STARTING_FEN,
) -> GameRecord:
    """
    Run an AI-vs-AI game and return a structured record.

    Args:
        white_depth: search depth in plies for White.
        black_depth: search depth in plies for Black.
        time_limit: optional time budget per move in seconds.
        use_alpha_beta: choose between alpha-beta pruning and plain minimax.
        max_moves: maximum number of full moves before stopping.
        fen: starting position in FEN notation.

    Returns:
        A GameRecord containing per-ply snapshots and the final result.
    """
    board = chess.Board(fen)
    record = GameRecord()

    for _ in range(max_moves * 2):  # max_moves full moves = 2x half-moves
        if board.is_game_over(claim_draw=True):
            break

        side_depth = white_depth if board.turn == chess.WHITE else black_depth
        result = choose_move(
            board,
            depth=side_depth,
            time_limit=time_limit,
            use_alpha_beta=use_alpha_beta,
        )
        if result.move is None or board.can_claim_draw():
            break

        record.plies.append(
            PlayRecord(
                fen_before=board.fen(),
                move_uci=result.move.uci(),
                score=result.score,
                nodes=result.nodes,
                elapsed=result.elapsed,
                depth=result.depth,
            )
        )
        board.push(result.move)

    record.final_fen = board.fen()
    record.result = board.result(claim_draw=True) if board.is_game_over(claim_draw=True) else "*"
    return record


def play_human_vs_ai(
    *,
    human_color: bool = chess.WHITE,
    ai_depth: int = 2,
    time_limit: Optional[float] = None,
    use_alpha_beta: bool = True,
    max_moves: int = 150,
    fen: str = chess.STARTING_FEN,
    input_fn: Callable[[str], str] = builtins.input,
    print_fn: Callable[[str], None] = builtins.print,
) -> GameRecord:
    """
    Run an interactive human-vs-AI game and return a structured record.

    On the human's turn, prompts for a UCI move (e.g. ``e2e4``) via
    *input_fn* and re-prompts on illegal input.  Entering ``quit`` or
    ``resign`` ends the game immediately.  The AI's turn calls the search
    engine exactly like :func:`play_game`.

    Args:
        human_color: ``chess.WHITE`` or ``chess.BLACK`` — the side the
            human controls.
        ai_depth: search depth in plies for the AI side.
        time_limit: optional time budget per AI move in seconds.
        use_alpha_beta: use alpha-beta pruning (True) or plain minimax.
        max_moves: maximum full moves before the game is stopped.
        fen: starting position in FEN notation.
        input_fn: callable used to read human input (injectable for tests).
        print_fn: callable used to display output (injectable for tests).

    Returns:
        A :class:`GameRecord` containing per-ply snapshots and the final
        result string (``"1-0"``, ``"0-1"``, ``"1/2-1/2"``, or ``"*"``).
    """
    board = chess.Board(fen)
    record = GameRecord()

    for _ in range(max_moves * 2):
        if board.is_game_over(claim_draw=True):
            break

        print_fn(board.unicode(invert_color=True, borders=True))
        print_fn(f"{'White' if board.turn == chess.WHITE else 'Black'} to move.")

        if board.turn == human_color:
            # Human turn
            while True:
                raw = input_fn("Your move (UCI, e.g. e2e4) or 'resign': ").strip().lower()
                if raw in {"quit", "resign"}:
                    record.final_fen = board.fen()
                    record.result = "0-1" if human_color == chess.WHITE else "1-0"
                    return record
                try:
                    move = chess.Move.from_uci(raw)
                except ValueError:
                    print_fn(f"Invalid UCI notation: {raw!r}. Try again.")
                    continue
                if move not in board.legal_moves:
                    print_fn(f"Illegal move in this position: {raw}. Try again.")
                    continue
                record.plies.append(
                    PlayRecord(
                        fen_before=board.fen(),
                        move_uci=move.uci(),
                        score=0.0,
                        nodes=0,
                        elapsed=0.0,
                        depth=0,
                    )
                )
                board.push(move)
                break
        else:
            # AI turn
            result = choose_move(
                board,
                depth=ai_depth,
                time_limit=time_limit,
                use_alpha_beta=use_alpha_beta,
            )
            if result.move is None or board.can_claim_draw():
                break
            print_fn(f"AI plays: {result.move.uci()}")
            record.plies.append(
                PlayRecord(
                    fen_before=board.fen(),
                    move_uci=result.move.uci(),
                    score=result.score,
                    nodes=result.nodes,
                    elapsed=result.elapsed,
                    depth=result.depth,
                )
            )
            board.push(result.move)

    record.final_fen = board.fen()
    record.result = board.result(claim_draw=True) if board.is_game_over(claim_draw=True) else "*"
    return record

