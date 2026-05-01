# CPTS 440 Chess Game-Playing Agent

Adversarial-search chess engine built on `python-chess`:

- Depth-limited minimax with alpha-beta pruning and deterministic MVV-LVA move ordering
- Evaluation function combining material, piece-square tables (PSTs), pawn structure, mobility, and king safety
- Iterative deepening with time-limited search
- AI-vs-AI game driver with per-move depth and timing metrics, HTML replay export
- Human-vs-AI interactive play via CLI or notebook
- Structured experiment runner for baseline-vs-improved and depth/time comparison matrices
- CLI for board inspection (`--mode inspect`) and interactive play (`--mode human`)
- Tests covering board helpers, evaluation, search correctness and performance, engine plumbing, and node-expansion comparisons

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

- CLI (play against the AI interactively)
  ```bash
  # Play as White against depth-2 AI
  python -m src.ui --mode human

  # Play as Black against depth-3 AI
  python -m src.ui --mode human --color black --depth 3

  # Start from a custom position
  python -m src.ui --mode human --fen "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
  ```
  Enter moves in UCI notation (e.g. `e7e5`). Type `resign` to end the game.

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

- Experiments and report generation
  ```python
  from src.experiments import build_default_matchups, run_matchups, write_metrics_bundle

  summaries = run_matchups(build_default_matchups(games=100))
  paths = write_metrics_bundle(summaries, "artifacts/experiments")
  print(paths["html"])  # Open the experiment report in a browser
  ```

## Test

```bash
pytest
```

## Project Structure

- `src/board.py`: board representation helpers and legal move utilities
- `src/search.py`: depth-limited minimax, alpha-beta pruning, iterative deepening, move ordering, `SearchResult` wrapper
- `src/eval.py`: evaluation function — material, piece-square tables, pawn structure, mobility, and king safety
- `src/engine.py`: top-level move selection, AI-vs-AI game runner (`play_game`), human-vs-AI runner (`play_human_vs_ai`), `GameRecord` with aggregate metrics
- `src/viz.py`: HTML replay generator for `GameRecord`
- `src/experiments.py`: structured AI-vs-AI batch runner and HTML/CSV/JSON report generation
- `src/ui.py`: CLI — board inspection (`--mode inspect`) and interactive human-vs-AI play (`--mode human`)
- `tests/`: smoke and correctness checks
- `demo.ipynb`: demonstration notebook covering engine overview, tactical puzzles, depth comparison, alpha-beta vs minimax, AI-vs-AI game replay, positional evaluation, structured experiments, and human-vs-AI play

## Notes
- Centipawn (scoring used for move evaluation): https://chess.fandom.com/wiki/Centipawn
