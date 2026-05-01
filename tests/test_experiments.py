import tempfile
from pathlib import Path

from src.experiments import MatchupSpec, StrategySpec, run_matchup, write_metrics_bundle


def test_run_matchup_produces_summary() -> None:
    spec = MatchupSpec(
        label="smoke",
        strategy_a=StrategySpec(label="white", depth=1),
        strategy_b=StrategySpec(label="black", depth=1),
        games=1,
        max_moves=1,
    )

    summary = run_matchup(spec)

    assert summary.games == 1
    assert len(summary.game_metrics) == 1
    assert summary.game_metrics[0].plies >= 0
    assert summary.game_metrics[0].white_time >= 0.0
    assert summary.game_metrics[0].black_time >= 0.0


def test_write_metrics_bundle_creates_files() -> None:
    spec = MatchupSpec(
        label="smoke",
        strategy_a=StrategySpec(label="white", depth=1),
        strategy_b=StrategySpec(label="black", depth=1),
        games=1,
        max_moves=1,
    )
    summary = run_matchup(spec)

    with tempfile.TemporaryDirectory() as tmp:
        paths = write_metrics_bundle([summary], Path(tmp))

        assert paths["json"].exists()
        assert paths["csv"].exists()
        assert paths["html"].exists()
        assert "AI-vs-AI Experiment Report" in paths["html"].read_text(encoding="utf-8")
