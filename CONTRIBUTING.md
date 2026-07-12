# Contributing to TTSTT

TTSTT's code style is deliberately distilled from Andrej Karpathy's recent teaching-repo
work (`nanochat`, `nanoGPT`, `micrograd`) and from `nerd-dictation`'s single-file
hackability. The goal: a tool a reader can open, understand end-to-end, and safely modify —
not a black box behind layers of abstraction. Every rule below exists to keep that true as
the codebase grows past a teaching repo into a real, long-lived tool. See the section at the
end for where — and why — we deliberately bend it.

## The rules

### 1. Minimal dependencies — each one must justify itself

Every third-party dependency is a cost: an attack surface, an upgrade treadmill, a black box
between you and the behavior you're debugging. Before adding one, ask: does the value it
provides outweigh what we lose in readability and control? Prefer the standard library
(`argparse` over `click`/`typer`, `unittest.mock`/stdlib over a mocking framework) unless the
dependency delegates genuinely hard, out-of-scope work (native inference engines, audio I/O,
config validation). `pyproject.toml`'s dependency list should be short enough to read in one
glance and justify in one sentence each.

### 2. Explicit over abstracted

Prefer a concrete function or class over a framework, plugin system, or metaprogramming
trick — even when it means a little repetition. If you can't point at the one place a piece
of behavior lives, it's too abstracted. Interfaces (protocols) are earned by a *second*
concrete implementation needing to swap in behind them, not created speculatively "in case."
See `activation/base.py`'s deliberately provisional protocol as the pattern: one concrete
implementation ships first; the protocol is extracted when the second implementation arrives.

### 3. Few files, one job each

Each module does one thing and is named for it (`audio.py` captures audio; `status.py`
reports status). Don't grow a module into a junk drawer — split it before "and" creeps into
its description. Don't fragment a single job across many files either — that's abstraction
by another name.

### 4. Derive config, don't expose it

Every user-facing config knob is a decision the user has to make and a case your code has to
handle. Expose the few knobs that materially matter (model, device, activation mode,
injection method) and derive everything else with sensible, documented defaults. If you're
tempted to add a flag "just in case someone wants to tune it," don't — add it when someone
actually needs it.

### 5. Surgical diffs

Change what the task requires and nothing else. Don't reformat, rename, or "clean up"
unrelated code in the same change — that buries the actual diff and makes review (and
`git blame`) useless. If something nearby genuinely needs fixing, do it as its own change.

### 6. Small, honest line counts

A module's line count should reflect what it actually does — no padding with defensive
boilerplate for cases that can't happen, no premature generalization "for later." If a module
is large, it's because its job is large, and that should be visible at a glance, not hidden
behind cleverness.

### 7. Machine-readable docs

`llms.txt` at the repo root is a project map — modules, their one-line jobs, and entry
points — kept current so an agent (or a new contributor) can navigate the codebase without
reading every file first. Update it in the same change that adds or moves a module.

## Where we bend for a real tool

TTSTT is not a teaching repo — it's a tool meant to run unattended on someone's desktop for
years. A handful of deliberate departures from the pure teaching-repo ethos exist because the
alternative would be worse, not because we abandoned rule 1–7:

- **Layered configuration (KTD6).** A real, multi-machine tool needs
  `defaults → config file → env → CLI flags` precedence and validation (Pydantic), not a
  single hardcoded dict. This is not a "config monster" — it's still governed by rule 4
  (derive, don't expose): the *mechanism* is layered so the tool is usable across machines
  and shells, but the *surface area* of exposed knobs stays small.
- **Error boundaries.** Native GPU libraries and Wayland IPC fail in ways that can abort the
  process uncatchably if unguarded (see KTD2's GPU warm-up, AE5). We add explicit boundaries
  — warm-up probes, capability detection, fallback chains — at exactly the points where a
  real desktop environment is allowed to misbehave. This is defensive code with a named
  failure mode behind it, not speculative boilerplate (which rule 6 still forbids).
- **Tests.** A teaching repo can be verified by reading it once. A daemon that runs for
  months, driven by a compositor keybind, cannot — regressions have to be caught before a
  user's desktop hangs. Tests exist for behavior that would otherwise only be caught by a
  human at 2am.
- **Packaging.** `pyproject.toml`, a `uv.lock`, a console entry point, and CI exist so the
  tool installs reproducibly on someone else's machine, not just the author's. This is the
  minimum packaging a distributable tool needs, following Karpathy's own `nanochat` toolchain
  choice (KTD8) rather than inventing something heavier.

## Licensing posture (R16)

TTSTT is a public repository that may be commercialized, so licensing is judged carefully —
**on the model *weights*, not just the code repository**, because the two can differ (e.g.
XTTS-v2's code is MPL-2.0 but its weights are non-commercial CPML; F5-TTS's code is MIT but
its base weights are CC-BY-NC).

- **Bundled defaults are permissive only: MIT, Apache-2.0, or BSD, code and weights alike.**
  Today that means `faster-whisper` (MIT), Silero VAD (MIT), openWakeWord (Apache-2.0),
  Kokoro-82M (Apache-2.0), and Chatterbox (MIT).
- **GPL and non-commercial engines are opt-in plugins the user installs explicitly — never
  bundled or enabled by default.** Piper (GPL) and non-commercially-licensed weights
  (XTTS-v2/CPML, F5-TTS base weights/CC-BY-NC) fall in this category if ever integrated.
- **Providers with usage caps or mandatory runtime credentials that conflict with the
  local-first, no-account premise are rejected outright** (e.g. Porcupine's 3-user cap and
  required runtime AccessKey).
- Before adding *any* new engine or voice as a bundled default, check both its code license
  and its weights' license, and record the check in the PR description.

## Before you submit

- `uv run ruff check .` is clean.
- `uv run pytest` is green, with no stray output (warnings, prints) polluting the run.
- New modules are reflected in `llms.txt`.
- The diff is surgical (rule 5) and the commit message explains *why*, not just *what*.
