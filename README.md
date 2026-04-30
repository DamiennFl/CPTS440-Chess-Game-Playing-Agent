# CPTS 440 Chess Game-Playing Agent

Adversarial-search chess engine built on `python-chess`, currently at the Week 2 milestone:

- Depth-limited minimax with alpha-beta pruning and simple move ordering
- Material-based evaluation (centipawns) and terminal scoring
- AI-vs-AI driver with game logging and HTML replay export
- Structured experiment runner for baseline-vs-improved and depth/time matrices
- Minimal CLI for FEN loading, listing/applying moves
- Tests covering board helpers, evaluation, search sanity/perf, engine plumbing, and node-expansion comparisons

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

- CLI (inspect a position, optionally apply a move)
  ```bash
  python -m src.ui
  python -m src.ui --fen "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
  python -m src.ui --fen "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1" --apply e1g1
  ```

- Programmatic search
  ```python
  import chess
  from src.search import choose_move

  board = chess.Board()
  result = choose_move(board, depth=2)  # SearchResult with move/score/nodes/depth
  print(result.move, result.score, result.nodes)

  # Optional comparison path for measuring pruning impact.
  baseline = choose_move(board, depth=2, use_alpha_beta=False)
  print(baseline.nodes, result.nodes)
  ```

- AI vs AI + replay export
  ```python
  from src.engine import play_game
  from src.viz import export_game_html

  game = play_game(white_depth=2, black_depth=2, max_moves=50)
  export_game_html(game, "out/game.html")  # Open in browser to step through moves
  ```

- Week 6 experiments + report generation
  ```python
  from src.experiments import build_week6_default_matchups, run_matchups, write_metrics_bundle

  summaries = run_matchups(build_week6_default_matchups(games=100))
  paths = write_metrics_bundle(summaries, "artifacts/experiments")
  print(paths["html"])  # Open the experiment report in a browser
  ```

## Test

```bash
pytest
```

## Project Structure

- `src/board.py`: board representation helpers and legal move utilities
- `src/search.py`: depth-limited minimax, alpha-beta pruning, move ordering, SearchResult wrapper
- `src/eval.py`: terminal handling + material evaluation (centipawns)
- `src/engine.py`: top-level move selection; AI-vs-AI game runner
- `src/viz.py`: HTML replay generator for GameRecord
- `src/experiments.py`: structured AI-vs-AI batch runner and HTML/CSV/JSON report generation
- `src/ui.py`: simple command-line interface
- `tests/`: smoke and correctness checks
- `demo.ipynb`: notebook scratchpad for quick experiments

## Week 6 / Week 7 Deliverables

- Week 6: run the structured matchup matrix, export `artifacts/experiments/experiment_summary.json`, `experiment_summary.csv`, and `experiment_report.html`.
- Week 7: finalize the notebook flow in `demo.ipynb`, reuse the generated HTML report and replay artifacts in the presentation, and keep the report claims aligned with the exported metrics.
- Week 7 slides: use [PRESENTATION_OUTLINE.md](PRESENTATION_OUTLINE.md) as the slide sequence and rehearsal checklist.
- Practice presentation: use the notebook sections as the demo script and rehearse with the generated HTML report open side-by-side.

## Notes
- Centipawn (scoring used for move evaluation): https://chess.fandom.com/wiki/Centipawn
