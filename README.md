# CPTS 440 Chess Game-Playing Agent

This repository contains Week 1 scaffolding for a chess AI project:

- Board-state handling using `python-chess`
- Modular architecture for search and evaluation
- A minimal CLI for loading positions, listing legal moves, and applying a move
- Tests for core board behavior and edge cases

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

```bash
python -m src.ui
python -m src.ui --fen "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
python -m src.ui --fen "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1" --apply e1g1
```

## Test

```bash
pytest
```

## Project Structure

- `src/board.py`: board representation helpers and legal move utilities
- `src/search.py`: search module interface (Week 2 minimax/alpha-beta implementation target)
- `src/eval.py`: evaluation interface
- `src/engine.py`: top-level move selection orchestration
- `src/ui.py`: simple command-line interface
- `tests/`: smoke and correctness checks

## Notes
- Centipawn (scoring used for move evaluation): https://chess.fandom.com/wiki/Centipawn
