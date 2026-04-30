from __future__ import annotations

import json
from pathlib import Path

import chess
import chess.svg

from src.engine import GameRecord


def export_game_html(game: GameRecord, path: str | Path) -> Path:
    """
    Self-contained HTML file that replays the game move-by-move.

    Features: play/pause, step forward/back, speed control, eval + move info.
    Returns the resolved output path.
    """
    frames: list[dict[str, str]] = []

    if game.plies:
        start_board = chess.Board(game.plies[0].fen_before)
    else:
        start_board = chess.Board(game.final_fen)

    frames.append({
        "svg": chess.svg.board(start_board, size=420),
        "label": "Start",
        "score": "0",
        "nodes": "",
        "elapsed": "",
        "depth": "",
    })

    # One frame per ply: show the board *after* the move with an arrow.
    for i, ply in enumerate(game.plies):
        board = chess.Board(ply.fen_before)
        move = chess.Move.from_uci(ply.move_uci)
        board.push(move)

        svg = chess.svg.board(
            board,
            size=420,
            lastmove=move,
        )

        side = "White" if i % 2 == 0 else "Black"
        move_num = i // 2 + 1
        label = f"{move_num}{'.' if i % 2 == 0 else '...'} {ply.move_uci} ({side})"

        frames.append({
            "svg": svg,
            "label": label,
            "score": f"{ply.score:+.0f}",
            "nodes": f"{ply.nodes:,}",
            "elapsed": f"{ply.elapsed:.3f}s" if ply.elapsed else "",
            "depth": str(ply.depth) if ply.depth > 0 else "",
        })

    frames_json = json.dumps(frames)

    html = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Chess Game Replay</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: system-ui, -apple-system, sans-serif;
    background: #1a1a2e;
    color: #e0e0e0;
    display: flex;
    justify-content: center;
    padding: 2rem;
  }}
  .container {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.2rem;
    max-width: 500px;
  }}
  h1 {{ font-size: 1.4rem; color: #fff; }}
  #board-container svg {{ display: block; }}
  .info-bar {{
    display: flex;
    gap: 2rem;
    font-size: 0.95rem;
    background: #16213e;
    padding: 0.6rem 1.2rem;
    border-radius: 6px;
    min-width: 420px;
    justify-content: space-between;
  }}
  .info-bar span {{ font-weight: 600; }}
  .controls {{
    display: flex;
    gap: 0.5rem;
    align-items: center;
    flex-wrap: wrap;
    justify-content: center;
  }}
  button {{
    background: #0f3460;
    color: #e0e0e0;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
  }}
  button:hover {{ background: #1a5276; }}
  button:disabled {{ opacity: 0.4; cursor: default; }}
  .speed-control {{
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.85rem;
  }}
  input[type=range] {{ width: 100px; accent-color: #0f3460; }}
  #result {{
    font-size: 1.1rem;
    font-weight: 700;
    color: #e2b714;
    min-height: 1.4rem;
  }}
</style>
</head>
<body>
<div class="container">
  <h1>Game Replay</h1>
  <div id="board-container"></div>
  <div class="info-bar">
    <div>Move: <span id="move-label">Start</span></div>
    <div>Eval: <span id="eval-score">0</span> cp</div>
    <div>Nodes: <span id="node-count"></span></div>
    <div>Depth: <span id="search-depth"></span></div>
    <div>Time: <span id="elapsed-time"></span></div>
  </div>
  <div class="controls">
    <button id="btn-start" title="Go to start">⏮</button>
    <button id="btn-prev" title="Step back">◀◀</button>
    <button id="btn-play" title="Play / Pause">▶</button>
    <button id="btn-next" title="Step forward">▶▶</button>
    <button id="btn-end" title="Go to end">⏭</button>
    <div class="speed-control">
      <label for="speed">Speed:</label>
      <input type="range" id="speed" min="25" max="200" value="100" step="25">
      <span id="speed-val">1x</span>
    </div>
  </div>
  <div id="result">{game.result if game.result != '*' else ''}</div>
</div>

<script>
const frames = {frames_json};
let idx = 0;
let timer = null;

const boardEl    = document.getElementById('board-container');
const labelEl    = document.getElementById('move-label');
const scoreEl    = document.getElementById('eval-score');
const nodesEl    = document.getElementById('node-count');
const depthEl    = document.getElementById('search-depth');
const timeEl     = document.getElementById('elapsed-time');
const playBtn    = document.getElementById('btn-play');
const speedInput = document.getElementById('speed');
const speedVal   = document.getElementById('speed-val');

function render() {{
  const f = frames[idx];
  boardEl.innerHTML = f.svg;
  labelEl.textContent = f.label;
  scoreEl.textContent = f.score;
  nodesEl.textContent = f.nodes;
  depthEl.textContent = f.depth;
  timeEl.textContent = f.elapsed;
}}

function stop() {{
  clearInterval(timer);
  timer = null;
  playBtn.textContent = '▶';
}}

function step(delta) {{
  const next = idx + delta;
  if (next < 0 || next >= frames.length) return;
  idx = next;
  render();
  if (idx === frames.length - 1) stop();
}}

document.getElementById('btn-start').onclick = () => {{ stop(); idx = 0; render(); }};
document.getElementById('btn-end').onclick   = () => {{ stop(); idx = frames.length - 1; render(); }};
document.getElementById('btn-prev').onclick  = () => {{ stop(); step(-1); }};
document.getElementById('btn-next').onclick  = () => step(1);

playBtn.onclick = () => {{
  if (timer) {{ stop(); return; }}
  if (idx >= frames.length - 1) idx = 0;
  playBtn.textContent = '⏸';
  timer = setInterval(() => step(1), getInterval());
}};

function getInterval() {{
  const multiplier = parseInt(speedInput.value) / 100;
  return Math.round(800 / multiplier);
}}

speedInput.oninput = () => {{
  const multiplier = parseInt(speedInput.value) / 100;
  speedVal.textContent = multiplier + 'x';
  if (timer) {{
    stop();
    playBtn.textContent = '\u23f8';
    timer = setInterval(() => step(1), getInterval());
  }}
}};

render();
</script>
</body>
</html>"""

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out.resolve()
