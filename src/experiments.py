from __future__ import annotations

import argparse
import csv
import html
import json
import re
from dataclasses import asdict, dataclass, field
from itertools import cycle
from pathlib import Path
from statistics import mean
from typing import Iterable, Optional, Sequence

import chess

from src.engine import GameRecord, PlayRecord, choose_move


@dataclass(frozen=True)
class StrategySpec:
    """Search configuration for one side in an experiment."""

    label: str
    depth: Optional[int] = None
    time_limit: Optional[float] = None
    use_alpha_beta: bool = True


@dataclass(frozen=True)
class MatchupSpec:
    """A repeated AI-vs-AI experiment pairing."""

    label: str
    strategy_a: StrategySpec
    strategy_b: StrategySpec
    games: int = 100
    max_moves: int = 80
    opening_fens: Sequence[str] = (chess.STARTING_FEN,)


@dataclass(frozen=True)
class GameMetrics:
    """Aggregated metrics for a single completed game."""

    matchup: str
    game_index: int
    opening_fen: str
    strategy_a_label: str
    strategy_b_label: str
    white_label: str
    black_label: str
    result: str
    plies: int
    white_nodes: int
    black_nodes: int
    white_time: float
    black_time: float
    white_avg_nodes: float
    black_avg_nodes: float
    white_avg_time: float
    black_avg_time: float


@dataclass
class MatchupSummary:
    """Summary across a batch of games for one matchup."""

    label: str
    strategy_a_label: str
    strategy_b_label: str
    games: int
    strategy_a_wins: int
    draws: int
    strategy_b_wins: int
    avg_plies: float
    avg_strategy_a_nodes: float
    avg_strategy_b_nodes: float
    avg_strategy_a_time: float
    avg_strategy_b_time: float
    game_metrics: list[GameMetrics] = field(default_factory=list)


def load_fens(path: str | Path) -> list[str]:
    """Load non-empty FEN lines from a file."""
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if text and not text.startswith("#"):
            rows.append(text)
    return rows


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    return slug.strip("-") or "experiment"


def _winner_from_result(result: str) -> str:
    if result == "1-0":
        return "white"
    if result == "0-1":
        return "black"
    return "draw"


def _average(values: Iterable[float]) -> float:
    values = list(values)
    return mean(values) if values else 0.0


def _play_single_game(
    white: StrategySpec,
    black: StrategySpec,
    *,
    opening_fen: str,
    max_moves: int,
) -> GameRecord:
    board = chess.Board(opening_fen)
    record = GameRecord()

    for _ in range(max_moves * 2):
        if board.is_game_over():
            break

        spec = white if board.turn == chess.WHITE else black
        result = choose_move(
            board,
            depth=spec.depth,
            time_limit=spec.time_limit,
            use_alpha_beta=spec.use_alpha_beta,
        )
        if result.move is None:
            break

        record.plies.append(
            PlayRecord(
                fen_before=board.fen(),
                move_uci=result.move.uci(),
                score=result.score,
                nodes=result.nodes,
                elapsed=result.elapsed,
            )
        )
        board.push(result.move)

    record.final_fen = board.fen()
    record.result = board.result(claim_draw=True) if board.is_game_over(claim_draw=True) else "*"
    return record


def _summarize_game(
    *,
    matchup: str,
    game_index: int,
    opening_fen: str,
    strategy_a_label: str,
    strategy_b_label: str,
    white_is_strategy_a: bool,
    record: GameRecord,
) -> GameMetrics:
    strategy_a_nodes = 0
    strategy_b_nodes = 0
    strategy_a_time = 0.0
    strategy_b_time = 0.0
    strategy_a_moves = 0
    strategy_b_moves = 0

    for ply in record.plies:
        board = chess.Board(ply.fen_before)
        is_strategy_a_turn = (board.turn == chess.WHITE and white_is_strategy_a) or (
            board.turn == chess.BLACK and not white_is_strategy_a
        )
        if is_strategy_a_turn:
            strategy_a_nodes += ply.nodes
            strategy_a_time += ply.elapsed
            strategy_a_moves += 1
        else:
            strategy_b_nodes += ply.nodes
            strategy_b_time += ply.elapsed
            strategy_b_moves += 1

    plies = len(record.plies)
    return GameMetrics(
        matchup=matchup,
        game_index=game_index,
        opening_fen=opening_fen,
        strategy_a_label=strategy_a_label,
        strategy_b_label=strategy_b_label,
        white_label=strategy_a_label if white_is_strategy_a else strategy_b_label,
        black_label=strategy_b_label if white_is_strategy_a else strategy_a_label,
        result=record.result,
        plies=plies,
        white_nodes=strategy_a_nodes if white_is_strategy_a else strategy_b_nodes,
        black_nodes=strategy_b_nodes if white_is_strategy_a else strategy_a_nodes,
        white_time=strategy_a_time if white_is_strategy_a else strategy_b_time,
        black_time=strategy_b_time if white_is_strategy_a else strategy_a_time,
        white_avg_nodes=(strategy_a_nodes if white_is_strategy_a else strategy_b_nodes) / max(1, strategy_a_moves if white_is_strategy_a else strategy_b_moves),
        black_avg_nodes=(strategy_b_nodes if white_is_strategy_a else strategy_a_nodes) / max(1, strategy_b_moves if white_is_strategy_a else strategy_a_moves),
        white_avg_time=(strategy_a_time if white_is_strategy_a else strategy_b_time) / max(1, strategy_a_moves if white_is_strategy_a else strategy_b_moves),
        black_avg_time=(strategy_b_time if white_is_strategy_a else strategy_a_time) / max(1, strategy_b_moves if white_is_strategy_a else strategy_a_moves),
    )


def run_matchup(spec: MatchupSpec) -> MatchupSummary:
    """Run a repeated AI-vs-AI matchup and return the summary."""
    opening_cycle = cycle(spec.opening_fens)
    game_metrics: list[GameMetrics] = []

    for game_index in range(spec.games):
        white_is_strategy_a = game_index % 2 == 0
        if white_is_strategy_a:
            white = spec.strategy_a
            black = spec.strategy_b
        else:
            white = spec.strategy_b
            black = spec.strategy_a

        opening_fen = next(opening_cycle)
        record = _play_single_game(
            white,
            black,
            opening_fen=opening_fen,
            max_moves=spec.max_moves,
        )
        game_metrics.append(
            _summarize_game(
                matchup=spec.label,
                game_index=game_index + 1,
                opening_fen=opening_fen,
                strategy_a_label=spec.strategy_a.label,
                strategy_b_label=spec.strategy_b.label,
                white_is_strategy_a=white_is_strategy_a,
                record=record,
            )
        )

    strategy_a_wins = 0
    draws = 0
    strategy_b_wins = 0
    for game in game_metrics:
        winner = _winner_from_result(game.result)
        white_is_strategy_a = game.white_label == game.strategy_a_label
        if winner == "white":
            if white_is_strategy_a:
                strategy_a_wins += 1
            else:
                strategy_b_wins += 1
        elif winner == "black":
            if white_is_strategy_a:
                strategy_b_wins += 1
            else:
                strategy_a_wins += 1
        else:
            draws += 1

    return MatchupSummary(
        label=spec.label,
        strategy_a_label=spec.strategy_a.label,
        strategy_b_label=spec.strategy_b.label,
        games=spec.games,
        strategy_a_wins=strategy_a_wins,
        draws=draws,
        strategy_b_wins=strategy_b_wins,
        avg_plies=_average(game.plies for game in game_metrics),
        avg_strategy_a_nodes=_average(
            game.white_nodes if game.white_label == game.strategy_a_label else game.black_nodes
            for game in game_metrics
        ),
        avg_strategy_b_nodes=_average(
            game.black_nodes if game.white_label == game.strategy_a_label else game.white_nodes
            for game in game_metrics
        ),
        avg_strategy_a_time=_average(
            game.white_time if game.white_label == game.strategy_a_label else game.black_time
            for game in game_metrics
        ),
        avg_strategy_b_time=_average(
            game.black_time if game.white_label == game.strategy_a_label else game.white_time
            for game in game_metrics
        ),
        game_metrics=game_metrics,
    )


def run_matchups(specs: Sequence[MatchupSpec]) -> list[MatchupSummary]:
    return [run_matchup(spec) for spec in specs]


def _summary_to_dict(summary: MatchupSummary) -> dict[str, object]:
    return {
        "label": summary.label,
        "strategy_a_label": summary.strategy_a_label,
        "strategy_b_label": summary.strategy_b_label,
        "games": summary.games,
        "strategy_a_wins": summary.strategy_a_wins,
        "draws": summary.draws,
        "strategy_b_wins": summary.strategy_b_wins,
        "avg_plies": summary.avg_plies,
        "avg_strategy_a_nodes": summary.avg_strategy_a_nodes,
        "avg_strategy_b_nodes": summary.avg_strategy_b_nodes,
        "avg_strategy_a_time": summary.avg_strategy_a_time,
        "avg_strategy_b_time": summary.avg_strategy_b_time,
        "games_detail": [asdict(game) for game in summary.game_metrics],
    }


def write_metrics_bundle(summaries: Sequence[MatchupSummary], out_dir: str | Path) -> dict[str, Path]:
    """Write JSON, CSV, and HTML report artifacts for an experiment batch."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    json_path = out_path / "experiment_summary.json"
    csv_path = out_path / "experiment_summary.csv"
    html_path = out_path / "experiment_report.html"

    json_path.write_text(
        json.dumps([_summary_to_dict(summary) for summary in summaries], indent=2),
        encoding="utf-8",
    )

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "matchup",
            "games",
            "strategy_a_wins",
            "draws",
            "strategy_b_wins",
            "avg_plies",
            "avg_strategy_a_nodes",
            "avg_strategy_b_nodes",
            "avg_strategy_a_time",
            "avg_strategy_b_time",
        ])
        for summary in summaries:
            writer.writerow([
                summary.label,
                summary.games,
                summary.strategy_a_wins,
                summary.draws,
                summary.strategy_b_wins,
                f"{summary.avg_plies:.2f}",
                f"{summary.avg_strategy_a_nodes:.2f}",
                f"{summary.avg_strategy_b_nodes:.2f}",
                f"{summary.avg_strategy_a_time:.4f}",
                f"{summary.avg_strategy_b_time:.4f}",
            ])

    html_path.write_text(render_report_html(summaries), encoding="utf-8")
    return {"json": json_path, "csv": csv_path, "html": html_path}


def _bar_svg(values: Sequence[tuple[str, float]], *, width: int = 520, height: int = 180) -> str:
    if not values:
        return "<svg width='520' height='180'></svg>"

    max_value = max(value for _, value in values) or 1.0
    bar_width = width / len(values)
    baseline = height - 30
    bars = []
    for index, (label, value) in enumerate(values):
        bar_height = (value / max_value) * (height - 50)
        x = index * bar_width + 20
        y = baseline - bar_height
        bars.append(
            f"<g><rect x='{x:.1f}' y='{y:.1f}' width='{bar_width - 40:.1f}' height='{bar_height:.1f}' rx='6' fill='#0f3460' />"
            f"<text x='{x + (bar_width - 40) / 2:.1f}' y='{height - 10}' fill='#e0e0e0' text-anchor='middle' font-size='12'>{html.escape(label)}</text>"
            f"<text x='{x + (bar_width - 40) / 2:.1f}' y='{y - 6:.1f}' fill='#e2b714' text-anchor='middle' font-size='12'>{value:.1f}</text></g>"
        )
    return f"<svg width='{width}' height='{height}' viewBox='0 0 {width} {height}'>{''.join(bars)}</svg>"


def render_report_html(summaries: Sequence[MatchupSummary]) -> str:
    sections = []
    for summary in summaries:
        outcome_chart = _bar_svg([
                        (html.escape(summary.strategy_a_label), float(summary.strategy_a_wins)),
            ("Draw", float(summary.draws)),
                        (html.escape(summary.strategy_b_label), float(summary.strategy_b_wins)),
        ])
        timing_chart = _bar_svg([
                        (html.escape(summary.strategy_a_label), summary.avg_strategy_a_time),
                        (html.escape(summary.strategy_b_label), summary.avg_strategy_b_time),
        ])
        sections.append(
            f"""
            <section class='card'>
              <h2>{html.escape(summary.label)}</h2>
                            <p><strong>Strategy A:</strong> {html.escape(summary.strategy_a_label)}<br>
                                 <strong>Strategy B:</strong> {html.escape(summary.strategy_b_label)}<br>
                 <strong>Games:</strong> {summary.games}</p>
              <div class='charts'>
                <div>
                  <h3>Results</h3>
                  {outcome_chart}
                </div>
                <div>
                  <h3>Average Move Time</h3>
                  {timing_chart}
                </div>
              </div>
              <table>
                                <tr><th>Strategy A wins</th><th>Draws</th><th>Strategy B wins</th><th>Avg plies</th><th>A nodes</th><th>B nodes</th></tr>
                <tr>
                                    <td>{summary.strategy_a_wins}</td>
                  <td>{summary.draws}</td>
                                    <td>{summary.strategy_b_wins}</td>
                  <td>{summary.avg_plies:.1f}</td>
                                    <td>{summary.avg_strategy_a_nodes:.1f}</td>
                                    <td>{summary.avg_strategy_b_nodes:.1f}</td>
                </tr>
              </table>
            </section>
            """
        )

    body = "\n".join(sections) if sections else "<p>No results.</p>"
    return f"""<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='utf-8'>
<title>Week 6 Experiment Report</title>
<style>
  body {{
    font-family: system-ui, -apple-system, sans-serif;
    margin: 0;
    background: linear-gradient(160deg, #0f172a, #111827 55%, #1f2937);
    color: #f3f4f6;
    padding: 2rem;
  }}
  .container {{ max-width: 1100px; margin: 0 auto; }}
  h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
  .subtitle {{ color: #cbd5e1; margin-bottom: 1.5rem; }}
  .card {{ background: rgba(15, 23, 42, 0.88); border: 1px solid #334155; border-radius: 16px; padding: 1.25rem; margin-bottom: 1.25rem; box-shadow: 0 10px 30px rgba(0,0,0,0.24); }}
  .charts {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; align-items: start; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
  th, td {{ border-bottom: 1px solid #334155; padding: 0.6rem 0.5rem; text-align: center; }}
  th {{ color: #cbd5e1; font-weight: 600; }}
  h2, h3 {{ margin: 0 0 0.75rem 0; }}
  svg {{ max-width: 100%; height: auto; }}
</style>
</head>
<body>
<div class='container'>
  <h1>Week 6 AI-vs-AI Experiment Report</h1>
  <p class='subtitle'>Structured matchup summaries with outcome distributions, average search effort, and per-game metrics.</p>
  {body}
</div>
</body>
</html>"""


def build_week6_default_matchups(games: int = 100) -> list[MatchupSpec]:
    """Convenience matchups for the Week 6 experiment matrix."""
    baseline = StrategySpec(label="Baseline Minimax d3", depth=3, use_alpha_beta=False)
    improved = StrategySpec(label="Improved AlphaBeta d3", depth=3, use_alpha_beta=True)
    shallow = StrategySpec(label="Improved AlphaBeta d2", depth=2, use_alpha_beta=True)
    timed = StrategySpec(label="Improved Iterative 0.15s", time_limit=0.15, use_alpha_beta=True)
    deeper = StrategySpec(label="Improved AlphaBeta d4", depth=4, use_alpha_beta=True)

    return [
        MatchupSpec(label="baseline-vs-improved", strategy_a=baseline, strategy_b=improved, games=games),
        MatchupSpec(label="depth-2-vs-depth-4", strategy_a=shallow, strategy_b=deeper, games=games),
        MatchupSpec(label="depth-3-vs-iterative-time", strategy_a=improved, strategy_b=timed, games=games),
    ]


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run structured AI-vs-AI chess experiments.")
    parser.add_argument("--games", type=int, default=100, help="Games per matchup.")
    parser.add_argument("--out-dir", default="artifacts/experiments", help="Output directory for JSON/CSV/HTML results.")
    args = parser.parse_args(argv)

    summaries = run_matchups(build_week6_default_matchups(games=args.games))
    paths = write_metrics_bundle(summaries, args.out_dir)

    print(f"Wrote experiment JSON: {paths['json']}")
    print(f"Wrote experiment CSV: {paths['csv']}")
    print(f"Wrote experiment HTML: {paths['html']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())