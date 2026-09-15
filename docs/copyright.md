# Copyright & License

Three layers, three regimes. Do not mix them.

## 1. Original Edo-period works — Public Domain

Works such as Ito Kanju's *Shogi Zuko* (1755; author d. 1760) and
Ito Sok an III's *Shogi Muso* (1734; author d. 1761) are in the public
domain in Japan and the United States by expiry of copyright.
No permission is required to transcribe the **facts** they contain
(piece placements, move sequences).

## 2. This project's dataset records — CC0 1.0

Newly created machine-readable records (`collections/**/*.json`,
generated SFEN/USI/KIF) are dedicated to the public domain under
**CC0 1.0 Universal** (see LICENSE-DATA, SPDX: `CC0-1.0`).
They contain only transcribed facts plus our own metadata — no text,
commentary, or images copied from modern sources.

## 3. Software — MIT License

Validators, converters, tests, CI configs, and the web viewer
(`tools/`, `tests/`, `.github/`, `web/`) are under the **MIT License**
(see LICENSE-CODE, SPDX: `MIT`).

## What we do NOT do

- Copy board diagrams, commentaries, essays, or solution texts from
  modern books, websites, or apps — even when the underlying classical
  problem is public domain. A modern transcription has its own rights.
- Treat "SFEN found on the internet" as provenance. Internet finds are
  collation references at most; dataset provenance always resolves to
  the primary source (see docs/provenance.md).
