# tiny-chess-4k

A chess engine in 4 KB of Python, built as an entry for the
[make.fun](https://make.fun) bounty **tiny-chess-01** ("4 KB 以内の Python
チェスエンジン" — a chess engine in at most 4 KB of Python).

- `main.py` — the submitted entrypoint (4,072 bytes): the readable source,
  packed with the competition kit's own `makefun compress` (LZMA stub).
- `src.py` — the readable source `main.py` was packed from.

## Design

- Board: a 120-character string (a1 = 91 … h8 = 28). After every move the
  board is rank-flipped and colours are swapped, so the side to move is
  always uppercase and every table faces one way.
- Evaluation: incremental and tapered (midgame/endgame blend by game
  phase) — material + piece-square tables (pawn and king have their own
  endgame tables), plus a bishop-pair bonus. The tables are stored as
  left halves only (they are file-symmetric) and expanded at startup.
- Search: iterative deepening under a fixed node budget (never a clock,
  so play is deterministic), negamax alpha-beta with a transposition
  table, quiescence search with delta pruning, null-move pruning,
  late-move reductions, check extensions, and move ordering by the
  evaluation delta of each move.

Python 3 standard library only; no model calls; the engine talks to the
competition environment over HTTP (`MAKEFUN_ENV_URL`).

## Local check

With the tiny-chess-01 dev kit unpacked next to this repo:

```
node <kit>/cli/makefun.mjs compress src.py --out main.py
```

## License

MIT (see `LICENSE`).
