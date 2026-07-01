---
title: "feat: TTSTT — local-first modular voice toolkit (STT + TTS)"
date: 2026-06-30
type: feat
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
execution: code
product_contract_source: ce-plan-bootstrap
depth: deep
plan_local_ids: [R, A, F, AE, U]
---

# feat: TTSTT — local-first modular voice toolkit (STT + TTS)

**Product Contract preservation:** Created by `ce-plan` (no upstream brainstorm). The Product Contract below was authored here from the user's request; treat it as the WHAT this plan commits to.

---

## Summary

TTSTT is a local-first, modular voice toolkit for Linux: speech-to-text (dictation) and
text-to-speech, with pluggable model backends that run locally on CPU/GPU/other accelerators
and connect to cloud providers through the same interface. It is built to be **readable and
hackable** in the spirit of Andrej Karpathy's recent work — minimal dependencies, explicit
over abstracted, few knobs with sensible derived defaults — while bending that teaching-repo
ethos where a real, long-lived tool demands it (layered config, error boundaries, tests,
packaging).

This plan delivers a **vertical slice** in implementation-ready detail — press a bound key,
speak, and have transcribed text injected into the focused application, end-to-end with
`faster-whisper` and `wtype` — built on the modular seams (STT backend, injector, activation,
config) that the full feature set plugs into. The slice deliberately validates **execution
mechanics**, not the product's differentiating premise: streaming-by-default and passive
wake-word listening (the capabilities no existing tool composes) live in the roadmap, and one
streaming milestone is pulled forward (Phase 3) to de-risk that core claim sooner. It then
sketches a **phased roadmap** for the remaining capabilities (VAD, streaming, wake-word
continuous listening, TTS with custom voices, TUI/GUI, OSD, cloud adapters) so the whole arc is
visible without over-specifying work that the slice will inform.

---

## Goal Capsule

**For** a Linux power user (Wayland/COSMIC) who currently "gets by" with `voxtype`,
**TTSTT** is a voice toolkit **that** provides local-first dictation and speech synthesis
with swappable models and direct text injection, **unlike** whisper-flow / Monologue (cloud,
closed, non-Linux) and unlike the current ad-hoc setup, **because** it is owned, modular,
hackable, and local by default.

**v1 done means:** a daemon-backed dictation loop where a compositor-bound keystroke toggles
listening, speech is transcribed locally by `faster-whisper`, and the text is injected into
the focused app via `wtype` (with clipboard-paste fast path) — installed and configured per
user by an onboarding command, on the user's COSMIC desktop.

---

## Problem Frame

The user wants to stop "getting by" with a patchwork dictation setup (`voxtype`) and own a
voice solution that is **local first, modular, and hackable**. Note on prior pain: the user's
voxtype trouble was primarily a **GPU device-index crash loop** (Vulkan/CUDA selecting the iGPU
instead of the RTX 3070), fixed by pinning the device (`gpu_device=1`) — not a broken COSMIC
keybind, which works (Super+KP_Add). So the motive is ownership, hackability, and the
capabilities voxtype lacks (notably streaming-by-default and a composed wake-word pipeline),
not a raw dictation capability gap. Comparable products (whisper-flow / Wispr Flow, Monologue)
are cloud, closed, and not Linux-native. The Linux OSS space has strong *pieces* —
`faster-whisper`, Silero VAD, openWakeWord, Kokoro, Chatterbox, `wtype`/`ydotool` — but **no
tool composes them** into a local-first package with all the activation modes (PTT, toggle,
VAD, passive continuous + wake word), streaming-by-default STT, first-class local TTS (base +
custom voices), direct Wayland/X11 injection, and a per-user onboarding + TUI/GUI/OSD surface.
TTSTT is that composition. (See **Alternatives Considered** for why greenfield over forking an
existing tool.)

Two environment realities shape the design from day one, **verified against the user's machine
and working voxtype setup**:
- **`wtype` works on the target COSMIC session.** COSMIC (`cosmic-comp` 1.0.0) exposes the
  Wayland virtual-keyboard protocol, and the user's working voxtype config already injects via
  `wtype` by default (`driver_order = ["wtype", "dotool", "ydotool", "clipboard"]`). So `wtype`
  + clipboard-paste is the **no-sudo default**, and `ydotool`/uinput is a fallback — not the
  only route. (The user is already in the `input` group with a `/dev/uinput` ACL, so the uinput
  path is available too if a non-COSMIC environment ever needs it.)
- **Global hotkeys on Wayland/COSMIC are restricted** — no in-process global grab — so
  activation binds a compositor keyboard shortcut to a control CLI. This restriction (and the
  need to host multiple activation modes), not any past keybind failure, is what justifies the
  daemon + control-CLI spine.

---

## Product Contract

### Actors

- **A1 — Dictating user.** A single Linux desktop user who triggers dictation and expects text
  to land in whatever app is focused.
- **A2 — Operator/installer.** The same user, in setup mode, running onboarding and editing
  preferences (TUI/GUI/config file).
- **A3 — Model/voice author.** The user supplying third-party voices or local samples to clone
  a custom TTS voice.
- **A4 — Compositor/OS.** Wayland (COSMIC/wlroots/KDE/GNOME) or X11, the uinput subsystem,
  PipeWire, and the focused application receiving injected text.

### Requirements

Each requirement carries a stable R-ID. **[v1]** = in the vertical slice; **[roadmap]** =
phased follow-up (design seams exist in v1).

- **R1 [v1]** — Local-first STT: transcribe microphone speech to text fully offline using a
  local model, with no network dependency in the default path.
- **R2 [v1]** — Pluggable STT backend: a single interface behind which `faster-whisper`,
  future streaming models, and cloud adapters are interchangeable.
- **R3 [v1]** — Backend runs on CPU or GPU, with the compute device user-selectable (honoring
  the user's RTX 3070).
- **R4 [v1]** — Toggle-based recording activation, driven by a compositor-bound keystroke via a
  control CLI.
- **R5 [v1]** — Direct text injection into the focused Wayland/X11 app, with a clipboard-paste
  fast path and runtime capability detection across compositors (must work on COSMIC).
- **R6 [v1]** — Layered, validated, per-user configuration (defaults → file → env → CLI flags)
  exposing few knobs with sensible derived defaults.
- **R7 [v1]** — Per-user onboarding command that checks dependencies/permissions, fetches the
  default model, writes config, and prints the exact compositor keybind to set.
- **R8 [v1]** — Minimal, non-blocking status feedback while listening/transcribing (desktop
  notification in v1; full OSD in roadmap).
- **R9 [roadmap]** — Additional STT activation modes: true hold push-to-talk, VAD-based
  endpointing, and passive continuous listening with wake-word activation.
- **R10 [roadmap]** — Streaming transcription as the default live mode, emitting stable partials
  (LocalAgreement-style) with incremental injection.
- **R11 [roadmap]** — Local-first TTS with a selection of base voices, importable third-party
  voices, and custom voices cloned from local samples.
- **R12 [roadmap]** — Pluggable TTS backend mirroring R2, with cloud TTS adapters.
- **R13 [roadmap]** — Cloud connectivity for both STT and TTS behind the same interfaces
  (opt-in, key-gated); credentials read from env/OS-keyring, never committed to config or logged.
- **R14 [roadmap]** — Default TUI with full parity for user preferences, plus an optional GUI
  install.
- **R15 [roadmap]** — Configurable, minimal-by-default on-screen display (OSD) overlay.
- **R16 [all]** — Licensing posture: only permissively licensed (MIT/Apache/BSD) engines ship as
  bundled defaults; GPL or non-commercial engines are available only as explicitly opt-in
  plugins, never bundled.

### Key Flows

- **F1 [v1] — Toggle dictation.** A1 presses the bound key → daemon starts capture → speaks →
  presses the key again → daemon stops capture, transcribes, injects text into the focused app,
  clears the status indicator.
- **F2 [v1] — First-run onboarding.** A2 runs `ttstt onboard` → tool checks PipeWire, probes
  the injector chain (`wtype` → clipboard → `ydotool`), verifies the downloaded model's hash,
  writes `config.toml`; prints the COSMIC keybind to bind to `ttstt toggle`.
- **F3 [roadmap] — Passive wake-word dictation.** Daemon idles listening → wake word detected →
  VAD endpoints the utterance → streaming STT transcribes → text injected → returns to idle.
- **F4 [roadmap] — Speak text (TTS).** A1 runs `ttstt say "<text>"` (or pipes stdin) → selected
  voice synthesizes audio → plays through the default output device.
- **F5 [roadmap] — Create custom voice.** A3 provides local samples → cloning backend builds a
  voice profile → voice becomes selectable for F4.

### Acceptance Examples

- **AE1 [v1]** — Given the daemon is running and a key is bound to `ttstt toggle`, when the user
  presses the key, says "open the pod bay doors", and presses again, then the focused text field
  receives the text "open the pod bay doors" within a few seconds.
- **AE2 [v1]** — Given no network connection, when the user performs AE1, then transcription
  still succeeds (the default path is fully offline).
- **AE3 [v1]** — Given the desktop is COSMIC 1.0.0, when injection runs, then text is delivered
  via `wtype` (or clipboard-paste), and any *text* clipboard content present before injection is
  restored afterward — restored only **after** the target app has consumed the paste, not
  immediately (non-text clipboard content, e.g. images, is out of v1 restore scope).
- **AE4 [v1]** — Given a fresh machine, when the user runs `ttstt onboard`, then it reports each
  dependency's status, selects a working injector (`wtype` on COSMIC) or fails with an actionable
  message (and non-zero exit) if *no* injector is available, and on success prints the exact
  `ttstt toggle` keybind command to set in COSMIC.
- **AE5 [v1]** — Given `device = "cuda"` is configured but CUDA or a compatible cuDNN is
  unavailable, when the daemon starts, then a controlled GPU warm-up transcribe detects the
  fault, logs a clear warning, and falls back to CPU — rather than aborting natively on the
  first real utterance.
- **AE6 [v1]** — Given a config file sets `model = "base"` and an env var overrides it to
  `small`, when the daemon starts, then the effective model is `small` (CLI > env > file >
  default precedence holds).

---

## Scope Boundaries

### In scope — vertical slice (v1, this plan's implementation units)

Daemon + control CLI; toggle activation bound to a compositor shortcut; local STT via
`faster-whisper` (CPU/GPU); `ydotool`/uinput injection + clipboard-paste fast path with runtime
capability detection; layered config; per-user onboarding; minimal desktop-notification status;
the modular seams (STT backend interface, injector interface, activation interface) that
roadmap work plugs into.

### Deferred to follow-up work — sketched roadmap (design seams land in v1)

See **Phased Roadmap** below. Includes: hold-PTT (evdev), VAD endpointing, streaming STT with
incremental injection, wake-word continuous listening, TTS (base voices, import, cloning), cloud
adapters, TUI, optional GUI, full OSD, additional injection backends (native `wtype`, `xdotool`,
IME). These are real planned work, sequenced after the slice — not non-goals.

### Outside this product's identity

- Not a general audio editor, meeting transcriber, or note-taking app.
- Not a cloud service or hosted product; cloud backends are opt-in adapters, never the default.
- Not Windows/macOS-first (cross-platform may come, but Linux/Wayland is the identity).
- Does not bundle GPL or non-commercial model weights as defaults (R16).

---

## High-Level Technical Design

**Why this section:** the system is a composition of many swappable components across a
long-running daemon and a control plane — the seams *are* the product, so their shape must be
explicit. Diagrams below are authoritative alongside the prose.

### Component architecture

```mermaid
graph TD
    subgraph CLI["ttstt CLI (control plane)"]
        TOGGLE["ttstt toggle / ptt"]
        ONBOARD["ttstt onboard"]
        CFG["ttstt config"]
        SAY["ttstt say (roadmap)"]
    end

    subgraph DAEMON["ttstt daemon (long-running)"]
        CTRL["Control socket\n(unix domain)"]
        ACT["Activation\n(interface)"]
        CAP["Audio capture\n(sounddevice)"]
        STT["STT backend\n(interface)"]
        INJ["Injector\n(interface)"]
        STATUS["Status / OSD\n(notify in v1)"]
    end

    subgraph BACKENDS["Pluggable implementations"]
        FW["faster-whisper (v1)"]
        STREAM["streaming STT (roadmap)"]
        CLOUDSTT["cloud STT (roadmap)"]
        WTYPE["wtype virtual-kbd (v1 default)"]
        CLIP["clipboard+paste (v1)"]
        YDO["ydotool / uinput (v1 fallback)"]
        XDO["xdotool / X11 (roadmap)"]
    end

    CONF["Config (TOML+env+CLI,\nPydantic)"]

    TOGGLE -->|socket cmd| CTRL
    CTRL --> ACT
    ACT -->|start/stop| CAP
    CAP -->|audio frames| STT
    STT -->|text| INJ
    ACT --> STATUS
    STT -.implements.- FW
    STT -.implements.- STREAM
    STT -.implements.- CLOUDSTT
    INJ -.implements.- WTYPE
    INJ -.implements.- CLIP
    INJ -.implements.- YDO
    INJ -.implements.- XDO
    CONF --> DAEMON
    ONBOARD --> CONF
    CFG --> CONF
```

### Dictation flow (F1, toggle)

```mermaid
sequenceDiagram
    actor User
    participant Compositor as COSMIC keybind
    participant CLI as ttstt toggle
    participant Daemon
    participant Capture as Audio capture
    participant STT as faster-whisper
    participant Inj as Injector
    participant App as Focused app

    User->>Compositor: press bound key
    Compositor->>CLI: run `ttstt toggle`
    CLI->>Daemon: socket: toggle
    Daemon->>Capture: start (status: listening)
    User->>Capture: speech
    User->>Compositor: press bound key again
    Compositor->>CLI: run `ttstt toggle`
    CLI->>Daemon: socket: toggle
    Daemon->>Capture: stop -> audio buffer
    Daemon->>STT: transcribe(buffer)
    STT-->>Daemon: text
    Daemon->>Inj: inject(text)
    Inj->>App: wtype (or clipboard-paste) -> text appears
    App-->>Inj: paste consumed
    Daemon->>Daemon: clear status, restore clipboard (after consume)
```

---

## Key Technical Decisions

- **KTD1 — Python core + native hot paths.** Python orchestration (daemon, CLI, config, glue)
  with performance-critical work delegated to native engines (`faster-whisper`/CTranslate2,
  ONNX runtimes) and `sounddevice`/PortAudio for capture. Matches the STT/TTS ecosystem, the
  whisper-flow/Monologue comparators, and the "readable/hackable" goal; reserves a future
  compiled hot path (e.g. capture/injection) only if profiling demands it. *(Confirmed with user.)*

- **KTD2 — Default STT = `faster-whisper` (int8), device-selectable.** One MIT codebase scales
  from CPU (`base`/`small`) to the RTX 3070 (`large-v3` int8 ≈ 2.9 GB). Compute device is a
  config knob; onboarding verifies the CUDA index rather than hardcoding it. The user's prior
  voxtype crash was a real GPU device-index fault (Vulkan selecting the iGPU over the 3070), and
  voxtype's Vulkan device index is *not* the same enumeration as faster-whisper's CUDA index —
  so the index must be probed on-machine, not copied across (see OQ1). A controlled GPU warm-up
  at startup converts otherwise-uncatchable native GPU-library aborts into a clean CPU fallback
  (AE5). True-streaming models (Nemotron-Streaming-0.6B GPU / Moonshine v2 CPU) are deferred to
  the streaming mode (R10) behind the same interface.

- **KTD3 — Injection = `wtype` (virtual-keyboard) default + clipboard-paste fast path +
  `ydotool`/uinput fallback.** *Verified on the target machine:* COSMIC 1.0.0 exposes the
  virtual-keyboard protocol and the user's voxtype already defaults to `wtype`
  (`driver_order = ["wtype", "dotool", "ydotool", "clipboard"]`), so `wtype` is the no-sudo v1
  default. Long/Unicode text uses clipboard+paste (save/restore clipboard, restoring only after
  the target consumes the paste). `ydotool`/uinput is the compositor-agnostic **fallback** for
  environments lacking the virtual-keyboard global (other compositors; X11 gets `xdotool` in the
  roadmap). A runtime capability probe orders the chain per detected globals — never trust
  compositor version numbers. This replaces the plan's original ydotool-first premise, which was
  wrong for COSMIC and manufactured an unnecessary no-sudo uinput dependency.

- **KTD4 — Activation spine = daemon + control CLI bound to a compositor shortcut; toggle
  first.** Wayland forbids in-process global hotkey grabs, and hosting multiple activation modes
  (toggle now; PTT/VAD/wake-word later) needs a resident process — this, not any past keybind
  failure, justifies the spine (the user's COSMIC keybind works today via Super+KP_Add). A single
  keybind → `ttstt toggle` over a unix socket is robust everywhere. True hold-PTT needs key
  *release* events (not delivered by compositor keybinds), so it is a roadmap unit via evdev or
  the XDG GlobalShortcuts portal.

- **KTD5 — Permissive-only defaults (R16).** Bundled defaults are MIT/Apache/BSD only:
  `faster-whisper` (MIT), Silero VAD (MIT), openWakeWord (Apache-2.0), Kokoro-82M (Apache-2.0),
  Chatterbox (MIT). GPL (Piper) and non-commercial (XTTS-v2/CPML, F5-TTS weights) engines are
  opt-in plugins the user installs explicitly, never shipped. Porcupine is rejected outright
  (3-user cap + runtime AccessKey). **Judge licensing on the model *weights*, not just the code
  repo** — the two can differ (XTTS-v2 code is MPL-2.0 but its weights are non-commercial CPML;
  F5-TTS code is MIT but its base weights are CC-BY-NC). This matters: TTSTT is a public Vulcan
  Neural repo that may be commercialized.

- **KTD6 — Layered config, few knobs (Karpathy "one dial").** `defaults → ~/.config/ttstt/
  config.toml → TTSTT_* env → CLI flags`, validated with Pydantic. Expose the few choices a user
  makes (model, device, activation mode, injection method); derive the rest. A real config
  system is *not* a "config monster" — this is the deliberate bend from the teaching-repo ethos.

- **KTD7 — Backend interfaces defined now, with ≥1 concrete impl each.** Modularity is a core
  product requirement, so the STT and Injector interfaces are the product and are defined in v1 —
  and both earn it immediately (Injector ships two real v1 impls, `wtype` + clipboard; STT's
  pluggability is an explicit v1 requirement, R2). The **Activation** interface is the exception:
  it has one trivial v1 impl (`ToggleActivation`) and its pluggability is roadmap (R9), so treat
  its protocol as *provisional* — implement `ToggleActivation` as a concrete class in v1 and
  extract the `Activation` protocol in Phase 2 when `PttActivation`/`VadActivation` arrive, so the
  seam is introduced by its second consumer rather than ahead of it. This keeps Karpathy's "no
  speculative abstraction" rule intact where it bites.

- **KTD8 — Packaging via `uv` + `pyproject.toml`, console entry point `ttstt`.** Mirrors
  Karpathy's own `nanochat` toolchain choice; minimal, reproducible, locked dependencies.

- **KTD9 — Audio capture = `sounddevice` (PortAudio).** NumPy-native callback streaming that
  rides PipeWire via PortAudio's ALSA/Pulse bridge on current distros. This binding is *not yet
  verified on the target* (the user's working setup uses whisper.cpp, not `sounddevice`), so
  onboarding runs a capture smoke-test (record → playback) confirming `sounddevice` enumerates
  the intended device, and names `python-rtmixer` (or a direct PipeWire path) as the fallback if
  it does not.

---

## Alternatives Considered

This is a from-scratch build with no upstream requirements doc validating the "build new"
premise, so the buy/extend-vs-build comparison is made explicit here:

- **Fix / extend `voxtype` (the current tool).** Lowest immediate cost — voxtype already does
  daily dictation on this COSMIC machine (working `wtype` injection, working Super+KP_Add keybind,
  GPU crash resolved). *Rejected as the primary path:* it is a Rust codebase less hackable than
  the stated Python/Karpathy goal, and lacks the streaming-by-default and composed wake-word
  pipeline that motivate TTSTT. It stays the fallback if TTSTT stalls, and its config
  (`driver_order`, `gpu_device`) is the reference for TTSTT's own defaults.
- **Fork `hyprvoice` or `whisrs`.** Both already implement a daemon + `wtype`/clipboard/ydotool
  injection loop — i.e. most of the v1 slice. *Rejected as the base:* hyprvoice is
  Hyprland-oriented and whisrs is Rust; adopting either forfeits the Python-hackability and clean
  backend-interface design that are the point. Used as **pattern references** (injection fallback
  chain, single-process daemon shape), not forked.
- **Greenfield (chosen).** Highest build cost, but the only path that delivers the readable,
  hackable, Python-first, fully-modular toolkit the goal describes. The vertical slice — and the
  U0 spike before it — keep that cost honest by proving mechanics before the roadmap expands.

**Cost check:** the v1 slice duplicates capability hyprvoice/whisrs already ship. That
duplication is accepted *only* because ownership, hackability, and the modular seams are the
product. If those stop mattering, forking hyprvoice is the cheaper route and this decision
should be revisited.

---

## Output Structure

```text
ttstt/
├── pyproject.toml              # uv-managed, console_scripts: ttstt
├── uv.lock
├── README.md
├── LICENSE                     # MIT
├── llms.txt                    # machine-readable project map (Karpathy agent-readiness)
├── CONTRIBUTING.md             # the Karpathy-derived style guide
├── docs/
│   └── plans/                  # this plan + future plans
├── src/ttstt/
│   ├── __init__.py
│   ├── __main__.py             # `python -m ttstt`
│   ├── cli.py                  # argparse command tree (toggle, onboard, config, daemon, spike)
│   ├── config.py               # layered config + Pydantic models
│   ├── daemon.py               # long-running loop + unix control socket (0600)
│   ├── audio.py                # sounddevice capture + ring buffer
│   ├── status.py               # minimal desktop-notification status (OSD later)
│   ├── onboarding.py           # dependency/permission checks + setup
│   ├── spike.py                # U0 one-shot record->transcribe->inject (pre-slice validation)
│   ├── stt/
│   │   ├── base.py             # STTBackend protocol
│   │   └── faster_whisper.py   # v1 implementation (+ GPU warm-up)
│   ├── inject/
│   │   ├── base.py             # Injector protocol + runtime capability detection + chooser
│   │   ├── wtype.py            # virtual-keyboard injector (v1 default)
│   │   ├── clipboard.py        # clipboard+paste fast path (v1, consume-then-restore)
│   │   └── ydotool.py          # uinput injector (v1 fallback)
│   └── activation/
│       ├── base.py             # Activation protocol (provisional; extracted in Phase 2)
│       └── toggle.py           # v1 toggle activation
└── tests/
    ├── test_config.py
    ├── test_audio.py
    ├── test_stt_faster_whisper.py
    ├── test_inject.py
    ├── test_activation.py
    ├── test_daemon.py
    └── test_onboarding.py
```

*The tree is a scope declaration; per-unit `Files` lists are authoritative and the implementer
may adjust the layout if implementation reveals a better one.*

---

## Implementation Units (vertical slice)

### U0. Feasibility spike — one-shot record → transcribe → inject

**Goal:** Before building any daemon/socket/interface machinery, prove the two genuinely
unvalidated environmental unknowns end-to-end on the target machine: (a) does `wtype`/clipboard
injection actually land text into the focused COSMIC app for this user, and (b) does
`faster-whisper` transcribe on the RTX 3070 (or fall back cleanly). A throwaway ~30–50 line
script, no abstractions.

**Requirements:** De-risks R1, R3, R5 before they are built out.

**Dependencies:** none (may precede U1; lives in `src/ttstt/spike.py` or a `scratch/` script).

**Files:** `src/ttstt/spike.py` (or `scratch/spike.py`), wired as a hidden `ttstt spike` command.

**Approach:** Record a few seconds of mic audio (sounddevice or a quick `pw-record` shell-out),
run one `faster-whisper` transcription (try `cuda`, catch/warm-up, else CPU), and inject the
text via `wtype` — printing which injector and device actually worked. No config system, no
daemon, no interfaces. Purpose is falsification: if injection or GPU transcription fails here,
the plan's defaults change before U2+ are built.

**Execution note:** This is a spike — delete or fold its learnings into U3/U4/U5 once the slice
exists. Do not grow it into the real capture/inject modules.

**Test scenarios:** Test expectation: none — throwaway validation script. Success is the manual
observation that text appears in a focused editor and transcription runs on the intended device.

**Verification:** On the user's COSMIC/3070 machine, running the spike types a spoken phrase into
a focused app and reports the working injector + compute device. Findings feed U3/U4/U5 defaults.

---

### U1. Project scaffold, tooling, and style guide

**Goal:** A runnable, lintable, testable Python package with the Karpathy-derived style guide
and machine-readable docs, so every later unit lands in a consistent home.

**Requirements:** Enables all; directly advances R16 (CONTRIBUTING records licensing posture).

**Dependencies:** none.

**Files:** `pyproject.toml`, `uv.lock`, `src/ttstt/__init__.py`, `src/ttstt/__main__.py`,
`src/ttstt/cli.py` (command stubs), `CONTRIBUTING.md`, `llms.txt`, `tests/` (pytest config),
`.github/workflows/ci.yml`.

**Approach:** `uv` project; `ruff` + `pytest` configured in `pyproject.toml`; console entry
point `ttstt = "ttstt.cli:main"`. `cli.py` defines the command tree (`toggle`, `daemon`,
`onboard`, `config`; `ptt` and `say` registered as explicit roadmap stubs that print
"not yet implemented") with handlers. `CONTRIBUTING.md` encodes the style rules
distilled from research: minimal dependencies (each must justify itself), explicit over
abstracted, few-files/one-job, derive config don't expose it, surgical diffs, small honest line
counts, machine-readable docs — with the explicit "where we bend for a real tool" section
(config, error handling, tests, packaging). `llms.txt` lists modules + entry points.

**Patterns to follow:** Karpathy `nanochat` toolchain (`uv`, vanilla deps); `nerd-dictation`
single-file hackability as the spiritual reference for module size.

**Test scenarios:**
- `ttstt --help` exits 0 and lists the command tree. (smoke)
- `ttstt --version` prints the version from package metadata.
- CI workflow runs `ruff check` and `pytest` and fails on lint/test error.
- Test expectation: scaffolding unit — coverage is the smoke/CLI wiring above; no domain logic yet.

**Verification:** `uv run ttstt --help` works; `ruff check` and `pytest` pass in CI.

---

### U2. Layered configuration system

**Goal:** One validated config object assembled from defaults → TOML file → env → CLI, exposing
few knobs, that every other component reads.

**Requirements:** R6; supports R3 (device), R4 (activation), R2/R5 (backend/injector selection).

**Dependencies:** U1.

**Files:** `src/ttstt/config.py`, `tests/test_config.py`, `src/ttstt/cli.py` (wire `ttstt
config get/set/path/show`).

**Approach:** Pydantic `Settings` model with nested sections (`stt`, `inject`, `activation`,
`audio`, `runtime`). Precedence: built-in defaults < `~/.config/ttstt/config.toml` (XDG) <
`TTSTT_*` env vars < explicit CLI flags. Few exposed knobs (model, device, activation mode,
injection method, language); derive the rest. `ttstt config show` prints the effective merged
config and the source of each value.

**Patterns to follow:** KTD6 "one dial"; XDG base-dir spec for paths.

**Test scenarios:**
- Covers AE6. File sets `model=base`, env `TTSTT_STT__MODEL=small` → effective is `small`.
- CLI flag overrides both env and file for the same key.
- Missing config file → defaults load without error and `config show` reports source "default".
- Invalid value (e.g. `device="banana"`) → validation error with an actionable message, non-zero exit.
- `config show` reports the correct source label (default/file/env/cli) per key.
- Unknown/extra keys in the TOML are rejected (or warned) rather than silently ignored.

**Verification:** `ttstt config show` reflects precedence; invalid config fails fast with a clear message.

---

### U3. Audio capture

**Goal:** Start/stop microphone capture into an in-memory buffer with selectable input device,
suitable for handing a complete utterance to STT.

**Requirements:** R1 (capture half of local STT); R6 (device config).

**Dependencies:** U1, U2.

**Files:** `src/ttstt/audio.py`, `tests/test_audio.py`.

**Approach:** `sounddevice` `InputStream` with a callback appending frames to a ring/accumulating
buffer; 16 kHz mono float32 (whisper's expected input). `start()`/`stop()` return the captured
buffer as a NumPy array. Input device resolved from config (default device when unset). Guard
against no-input-device and stream-overflow conditions with clear errors.

**Patterns to follow:** `sounddevice` callback streaming examples; KTD9.

**Test scenarios:**
- start→feed synthetic frames via injected fake stream→stop returns a contiguous float32 buffer of expected length. (use a fake/mock stream — no real mic in CI)
- Stop without start is a no-op (no crash, returns empty/None per contract).
- Configured non-existent device → actionable error, non-zero path.
- Buffer is correctly shaped (mono, 16 kHz) for the STT contract.
- Overflow/underflow callback flag is surfaced (logged), not silently dropped.

**Verification:** A scripted capture of a fixture WAV played through a virtual source yields a buffer STT can consume (manual/integration); unit tests pass against a faked stream.

---

### U4. STT backend interface + `faster-whisper` implementation

**Goal:** A pluggable STT seam with a working local implementation that transcribes an audio
buffer to text on CPU or the user's GPU.

**Requirements:** R1, R2, R3.

**Dependencies:** U1, U2.

**Files:** `src/ttstt/stt/base.py`, `src/ttstt/stt/faster_whisper.py`,
`tests/test_stt_faster_whisper.py`.

**Approach:** `STTBackend` protocol with `transcribe(audio: np.ndarray) -> str` and a
forward-declared streaming signature (`stream(frames) -> Iterator[Partial]`) that v1 leaves
unimplemented (documented `NotImplementedError`) so the streaming roadmap unit slots in without
interface churn. `FasterWhisperBackend` loads a model per config (`model`, `device`,
`compute_type=int8`/`int8_float16`) and transcribes. **Model integrity:** pin each model to a
specific hub revision/commit and verify the downloaded artifact against its published hash over
HTTPS before load, failing closed on mismatch — weight loaders are a supply-chain/RCE vector and
the download runs unattended in onboarding (see U8). **GPU robustness:** on `device="cuda"`, run
a controlled warm-up transcribe at construction so an otherwise-uncatchable native GPU-library
abort (e.g. cuDNN version mismatch, which surfaces on the *first* real transcribe, not at
`WhisperModel()` construction) is turned into a clean CPU fallback; pin the `cudnn-cu12` version
in the uv lock to reduce mismatch risk.

**Patterns to follow:** `faster-whisper` `WhisperModel` API; KTD2, KTD7.

**Test scenarios:**
- Covers AE2. Transcribe a short fixture WAV ("testing one two three") with the smallest model → output contains the expected words (tolerant match). (integration; gated/marked so CI can skip the model download, run locally)
- Covers AE5. `device="cuda"` with CUDA unavailable → warm-up detects the fault, logs warning, transcribes on CPU, no native abort on first utterance.
- Model hash mismatch (faked bad artifact) → load fails closed with an actionable error; no partial/tampered model is used.
- Empty/silent buffer → empty or whitespace string, no exception.
- Backend honors the configured model/device (assert constructor args via a thin seam/mock).
- Protocol conformance: `FasterWhisperBackend` satisfies `STTBackend`; calling `stream()` raises documented `NotImplementedError`.

**Verification:** Local run transcribes a fixture clip correctly on CPU and on `cuda`; the warm-up CPU-fallback path is exercised with CUDA/cuDNN disabled; a tampered-weight artifact is rejected.

---

### U5. Injector interface + `wtype` default + clipboard-paste fast path + `ydotool` fallback

**Goal:** Deliver transcribed text into the focused application reliably on COSMIC (via `wtype`)
and other compositors, with runtime capability detection and a safe clipboard round-trip.

**Requirements:** R5, R16 (only permissive tools).

**Dependencies:** U1, U2.

**Files:** `src/ttstt/inject/base.py`, `src/ttstt/inject/wtype.py`,
`src/ttstt/inject/clipboard.py`, `src/ttstt/inject/ydotool.py`, `tests/test_inject.py`.

**Approach:** `Injector` protocol `inject(text: str) -> None` plus a `capabilities()` probe that
detects, at runtime: the virtual-keyboard Wayland global (drives `wtype`), `wl-copy`/`wl-paste`,
`ydotoold` availability + uinput access, and X11/XWayland. `WtypeInjector` types via the
virtual-keyboard protocol (v1 default on COSMIC). `ClipboardInjector` saves current clipboard →
sets text → synthesizes paste (Ctrl+V, with terminal Ctrl+Shift+V awareness) → **waits for the
target to consume the paste (bounded settle) before restoring** — restoring immediately races the
async Wayland clipboard read and can paste stale content. `YdotoolInjector` (uinput) is the
fallback where the virtual-keyboard global is absent. `select_injector(config, capabilities)`
chooses: explicit config override, else `wtype`, else clipboard-paste for long/Unicode text, else
`ydotool`. Never trust version numbers — branch on detected globals.

**Privacy note (clipboard path):** the clipboard fast path transits transcribed speech (possibly
secrets) through the system clipboard, where clipboard-history managers snapshot it — restoring
the prior value does not un-snapshot it. Expose a config knob (`inject.sensitive = "type"`) that
forces `wtype`/`ydotool` typing (no clipboard transit) and make clipboard-paste opt-in for
arbitrary text, not automatic.

**Patterns to follow:** `voxtype` `driver_order = ["wtype", "dotool", "ydotool", "clipboard"]`
(the working config on this machine); `hyprvoice` fallback chain; KTD3.

**Test scenarios:**
- Covers AE3. Clipboard injector saves a sentinel clipboard value, injects text, restores the sentinel **only after** a simulated consume signal (assert ordering via faked `wl-copy`/`wl-paste`, not just final state).
- `select_injector` picks `wtype` on COSMIC-shaped capabilities (virtual-keyboard global present); picks clipboard-paste for long/Unicode; falls to `ydotool` only when the global is absent (table test).
- `wtype` injector formats the virtual-keyboard invocation correctly (assert command construction against a fake subprocess).
- Missing virtual-keyboard global AND missing uinput → selector surfaces an actionable "no injector available" error.
- `inject.sensitive = "type"` forces a typing injector and never touches the clipboard.
- Unicode/emoji text round-trips intact through the clipboard path.

**Verification:** On the user's COSMIC desktop, injecting a known string via `wtype` lands it in a
focused editor; a non-faked on-target test confirms the clipboard-restore timing (prior clipboard
intact, no stale paste); capability probe output matches the live environment.

---

### U6. Activation interface + toggle activation

**Goal:** Translate control commands into listen-start/stop events behind a swappable interface,
with toggle as the v1 implementation.

**Requirements:** R4; seam for R9 (PTT/VAD/wake-word).

**Dependencies:** U1, U2.

**Files:** `src/ttstt/activation/base.py`, `src/ttstt/activation/toggle.py`,
`tests/test_activation.py`.

**Approach:** `ToggleActivation` holds a boolean state advanced by a `toggle()` call (invoked by
the daemon when the control socket receives `toggle`): odd press → start, even press → stop. Per
KTD7 the `Activation` *protocol* is **provisional in v1** — ship `ToggleActivation` as a concrete
class and keep `base.py` a thin placeholder; formally extract the protocol in Phase 2 when
`PttActivation` (evdev key down/up) and `VadActivation`/`WakeWordActivation` become its second
consumers, so the seam is introduced by its second implementation rather than ahead of it.

**Patterns to follow:** KTD4, KTD7.

**Test scenarios:**
- First `toggle()` emits StartListening; second emits StopListening; alternation holds across N toggles.
- Reset/initial state is "not listening" (no spurious start on construction).
- Protocol conformance: `ToggleActivation` satisfies `Activation`.
- Concurrent toggles serialize to a consistent state (no lost/duplicated transition).

**Verification:** Driving `toggle()` in sequence yields the correct start/stop event stream.

---

### U7. Daemon + control CLI (integration spine)

**Goal:** The long-running process that wires capture → STT → injection, controlled over a unix
socket by `ttstt toggle`, with minimal status feedback. This is where the slice becomes a
working dictation loop.

**Requirements:** R1, R2, R4, R5, R8 (integrates U2–U6).

**Dependencies:** U2, U3, U4, U5, U6.

**Files:** `src/ttstt/daemon.py`, `src/ttstt/status.py`, `src/ttstt/cli.py` (implement
`ttstt daemon` and `ttstt toggle`; `ttstt ptt` stays a roadmap stub in v1), `tests/test_daemon.py`.

**Approach:** `ttstt daemon` opens a unix domain socket in the XDG runtime dir, **created with
`0600` perms** so only the owning user can send commands (the socket is a keystroke-injection
trigger — a resident process that types into the focused app on command; XDG_RUNTIME_DIR's `0700`
is the primary guard, `0600` on the socket is the explicit belt-and-suspenders). It constructs
the configured Activation/STT/Injector and runs an event loop: on StartListening →
`audio.start()` + status "listening"; on StopListening → `audio.stop()` → `stt.transcribe()`
(status "transcribing") → `injector.inject()` → clear status. `ttstt toggle` is a thin client
that connects to the socket and sends `toggle` (and prints an actionable error if the daemon
isn't running). `status.py` shows a minimal desktop notification (libnotify via `notify-send` or
`gi`), explicitly the v1 stand-in for the roadmap OSD. STT runs off the capture/IO path
(thread/async) so the control socket stays responsive.

**Patterns to follow:** `whisrs`/`hyprvoice` single-process daemon shape; KTD4.

**Test scenarios:**
- Covers AE1 (integration). With fake capture (fixture buffer), a stub STT returning a known
  string, and a fake injector, a `toggle`→`toggle` sequence over the socket results in the
  injector receiving exactly that string. (This is the load-bearing integration test mocks alone
  can't prove — it exercises the full wire.)
- `ttstt toggle` with no daemon running → actionable error + non-zero exit (does not hang).
- Daemon survives an STT exception on one utterance (logs, clears status, stays ready for the next).
- Status transitions listening → transcribing → idle in order; status is cleared even when injection fails.
- Two rapid toggles don't start two concurrent captures (state guarded).
- Socket is created in the runtime dir with `0600` perms and cleaned up on daemon shutdown.

**Verification:** On the user's machine, `ttstt daemon` + a bound key performs F1 end-to-end (AE1); killing/restarting the daemon recreates the socket cleanly.

---

### U8. Onboarding command (per-user setup)

**Goal:** A first-run command that checks dependencies/permissions, fetches the default model,
writes config, and tells the user exactly how to bind the toggle key in COSMIC.

**Requirements:** R7; supports R3 (device probe), R5 (injector-chain probe), R8.

**Dependencies:** U2, U4, U5.

**Files:** `src/ttstt/onboarding.py`, `src/ttstt/cli.py` (implement `ttstt onboard`),
`tests/test_onboarding.py`.

**Approach:** `ttstt onboard` runs ordered checks, each reporting OK / actionable-fix:
**(1) Audio** — PipeWire present + an input device, plus a `sounddevice` capture smoke-test
(record → playback) confirming the PortAudio↔PipeWire binding actually enumerates the device
(KTD9); name the `python-rtmixer` fallback if it fails. **(2) Injector** — probe the chain and
report which injector is active: `wtype` (virtual-keyboard global present, expected on COSMIC) →
clipboard (`wl-copy`/`wl-paste`) → `ydotool`/uinput. Only fail hard if *no* injector is
available. For the `ydotool` fallback, check *actual* uinput access (device ACL/perms), not
merely `input`-group membership, since group membership alone does not always grant access.
**(3) GPU** — optional CUDA probe reporting the CUDA device index for the RTX 3070 (distinct from
voxtype's Vulkan index — OQ1); CPU mode otherwise. **(4) Model** — download the default
`faster-whisper` model pinned to a revision and **verify its published hash** before use
(fail closed on mismatch). Then write a starter `config.toml` if absent and print the COSMIC
keybind instruction (bind a custom shortcut to `ttstt toggle`).

**Patterns to follow:** KTD3 (injector chain), KTD4 (COSMIC keybind guidance), KTD5 (only checks
for permissive tools).

**Test scenarios:**
- Covers AE4. All deps faked-present → exits 0, selects `wtype`, writes config if missing, prints the `ttstt toggle` keybind instruction.
- Covers AE4. No injector available (faked: no virtual-keyboard global, no uinput) → actionable "no injector" message + non-zero exit. A missing `ydotool` alone does NOT fail when `wtype` works.
- Capture smoke-test fails (faked) → reports the `python-rtmixer` fallback guidance, non-zero or warn per severity.
- Model hash mismatch (faked) → refuses the artifact, clear error, non-zero, config left consistent.
- Existing config is not clobbered (idempotent re-run; reports "config exists").
- CUDA-present probe reports the discrete-GPU CUDA index; CUDA-absent reports CPU mode without error.
- uinput fallback check distinguishes real ACL access from bare group membership.

**Verification:** On the user's COSMIC machine, `ttstt onboard` from clean state selects `wtype`,
runs the capture smoke-test, verifies the model hash, writes config, and the printed keybind
makes AE1 work.

---

## Phased Roadmap (post-slice, sketched)

Each phase plugs into the v1 seams; detailed implementation units will be planned when reached.
Ordering reflects dependency + value to the user's daily dictation.

- **Phase 2 — Richer STT activation.** `PttActivation` (true hold-to-talk via evdev or XDG
  GlobalShortcuts portal — needs key release events); `VadActivation` (Silero VAD endpointing →
  auto-stop on silence). *(R9)*
- **Phase 3 — Streaming-by-default.** Add a streaming STT backend (Nemotron-Streaming-0.6B on
  GPU / Moonshine v2 or sherpa-onnx Zipformer on CPU) behind `STTBackend.stream()`; incremental
  injection using LocalAgreement-n stable-prefix logic. Make streaming the default live mode.
  *(R10)*
- **Phase 4 — Passive continuous + wake word.** Compose openWakeWord (gate) → Silero VAD
  (endpoint) → streaming STT → injection — the pipeline no OSS tool ships today (F3). *(R9, R10)*
- **Phase 5 — TTS foundation.** `TTSBackend` interface + Kokoro-82M base voices; `ttstt say` and
  stdin piping; audio output via `sounddevice`. *(R11, R12, F4)*
- **Phase 6 — Voice import + cloning.** Third-party voice import (Kokoro voice packs / Piper
  `.onnx` as opt-in) and custom cloning from local samples via Chatterbox (note: mandatory Perth
  watermark on all output). *(R11, F5)*
- **Phase 7 — Cloud adapters.** STT/TTS cloud backends behind the same interfaces (Deepgram,
  OpenAI, ElevenLabs, …), opt-in and key-gated. **Credential-handling acceptance criterion:**
  API keys are read from env or an OS keyring — **never** from a committed `config.toml` (this is
  a public repo), never written to logs, with documented rotation and dev/prod env separation.
  *(R13)*
- **Phase 8 — TUI parity.** Textual-based TUI with full parity for all preferences. *(R14)*
- **Phase 9 — Full OSD.** `gtk4-layer-shell` overlay (minimal-by-default, configurable), with a
  plain top-level fallback on GNOME (no wlr-layer-shell). *(R15)*
- **Phase 10 — Optional GUI + more injectors.** Optional GUI install; native `wtype`, `xdotool`/
  X11, and IME injectors behind the existing `Injector` seam.

---

## Risks & Dependencies

- **Injection capability detection (medium).** The v1 default (`wtype`) is verified working on
  the target COSMIC 1.0.0, but other environments may lack the virtual-keyboard global.
  *Mitigation:* runtime probe orders `wtype` → clipboard → `ydotool`/uinput; onboarding reports
  the active injector. The `ydotool` fallback needs uinput access — already satisfied on the
  target (user in `input` group + `/dev/uinput` ACL), but onboarding checks *actual* ACL/perms,
  not bare group membership. (This risk was the plan's original #1 "no-sudo uinput" concern —
  demoted after verifying `wtype` is the working no-sudo default here.)
- **Model-weight supply chain (medium).** Unpinned/unverified weight downloads are an RCE/integrity
  vector and run unattended in onboarding. *Mitigation:* pin hub revision + verify published hash
  over HTTPS, fail closed (U4/U8).
- **Clipboard-history exposure (medium).** The clipboard fast path transits dictated text (possibly
  secrets) where history managers snapshot it. *Mitigation:* `inject.sensitive = "type"` knob
  forces typing; clipboard-paste opt-in for arbitrary text (U5).
- **Compositor capability gaps (medium).** GNOME's Mutter lacks wlr-layer-shell (OSD) and the
  virtual-keyboard global (`wtype`). *Mitigation:* runtime capability detection throughout;
  `ydotool`/uinput injection fallback; OSD top-level fallback in Phase 9 — never trust version
  numbers.
- **GPU device selection (medium).** The user's prior voxtype failure was a real GPU device-index
  crash loop (iGPU vs RTX 3070) — the most impactful past issue. *Mitigation:* onboarding probes
  and reports the CUDA index (distinct from voxtype's Vulkan index); config knob; GPU warm-up →
  CPU fallback (AE5). See OQ1.
- **Model licensing drift (medium).** Engine licenses shift (Piper → GPL-3.0; XTTS non-commercial;
  Porcupine caps), and *weights* can carry different terms than code. *Mitigation:* R16 posture
  enforced in CONTRIBUTING (judged on weights, KTD5) + a license note per bundled engine; GPL/NC
  engines opt-in only.
- **Streaming complexity (medium, deferred).** True streaming + stable-partial injection is the
  hardest later work. *Mitigation:* isolate behind `STTBackend.stream()`; adopt the proven
  LocalAgreement-n algorithm (whisper_streaming / WhisperLiveKit) rather than inventing one.
- **Chatterbox watermark (low, deferred).** All cloned-voice output carries a mandatory Perth
  watermark. *Mitigation:* disclose in TTS docs; offer permissive alternatives where they exist.

**External dependencies:** `uv`, PipeWire, `wtype` (present on target), `wl-clipboard` (present),
`ydotool`/`ydotoold` (fallback, optional), CTranslate2/`faster-whisper`, `sounddevice`/PortAudio,
a CUDA runtime + matched cuDNN (optional, for GPU).

---

## Verification Contract

- **Gate 0 — Spike (pre-slice):** U0 confirms `wtype` injection and 3070 transcription end-to-end
  on-target before U2+ are built.
- **Gate 1 — Static:** `ruff check` clean; `pytest` green (model-download integration tests
  marked and runnable locally, skippable in CI).
- **Gate 2 — Unit:** each unit's enumerated test scenarios pass.
- **Gate 3 — Integration (the spine):** the U7 toggle→toggle→inject test passes with faked
  capture/STT/injector (AE1 wired without hardware).
- **Gate 4 — Manual on-target (COSMIC):** AE1 (dictate→inject via `wtype`), AE3 (clipboard
  restore *timing* — a non-faked test), AE4 (onboarding + injector selection), AE5 (GPU
  warm-up → CPU fallback) verified on the user's machine.
- **Offline check:** AE2 — full default path succeeds with networking disabled.

---

## Definition of Done

- U0 spike has validated `wtype` injection + 3070 transcription on-target before the slice is built.
- Units U1–U8 implemented; all per-unit test scenarios and the Verification Contract gates pass.
- `ttstt onboard` brings a clean COSMIC machine to a working state (selects `wtype`, verifies the
  model hash, runs the capture smoke-test) and prints the correct keybind.
- AE1–AE6 hold on the user's RTX 3070 / COSMIC desktop, including the offline and CPU-fallback paths.
- `CONTRIBUTING.md` (Karpathy style guide + bend-for-production section), `README.md`, and
  `llms.txt` are present and accurate.
- Repo pushed to `github.com/vulcanneural/ttstt` (public) with CI green.
- Only permissively licensed engines are bundled, judged on weights (R16/KTD5 hold).

---

## Open Questions

- **OQ1 — CUDA device index for the RTX 3070.** The prior `voxtype` `gpu_device=1` fix was a
  Vulkan device index (voxtype uses a Vulkan/whisper.cpp backend), which is *not* the same
  enumeration as the CUDA device index `faster-whisper`/CTranslate2 uses. *Resolve at
  implementation:* `ttstt onboard` enumerates CUDA devices and reports the correct index; default
  config leaves it unset (auto) until verified on-machine.
- **OQ2 — Toggle vs hold-PTT as the daily default.** The slice ships toggle (robust on COSMIC).
  True hold-PTT needs evdev or the GlobalShortcuts portal. Worth deciding in Phase 2 whether
  evdev (needs input-group access, like uinput) or the portal (sudo-free but less mature) is the
  primary PTT path. *Deferred to Phase 2.*
- **OQ3 — uinput access without sudo (fallback only).** Now low-stakes for v1 since `wtype` is
  the no-sudo default and the user already has uinput access; matters only for the `ydotool`
  fallback on non-COSMIC machines or for evdev-based PTT. Whether a sudo-free path (portal/libei)
  beats the one-time udev/group setup. *Deferred; investigate in Phase 2.*
- **OQ4 — Streaming default model on 8 GB VRAM.** Nemotron-Streaming-0.6B vs Kyutai STT vs
  sherpa-onnx Zipformer on the 3070 alongside other GPU use. *Deferred to Phase 3 (benchmark).*

---

## Sources & Research

Research conducted 2026-06-30 (three parallel research streams; all license-critical claims
cross-checked against primary sources).

**Coding style (Karpathy):**
- microgpt (2026): http://karpathy.github.io/2026/02/12/microgpt/
- nanochat (README + toolchain): https://github.com/karpathy/nanochat
- nanoGPT / minGPT / micrograd: https://github.com/karpathy/nanoGPT · https://github.com/karpathy/minGPT · https://github.com/karpathy/micrograd
- "Software Is Changing (Again)" (YC, 2025): https://www.ycombinator.com/library/MW-andrej-karpathy-software-is-changing-again · writeup: https://www.latent.space/p/s3

**STT engines:** faster-whisper https://github.com/SYSTRAN/faster-whisper · Moonshine https://github.com/moonshine-ai/moonshine · Parakeet-TDT-0.6b-v3 https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3 · Nemotron-Speech-Streaming https://huggingface.co/nvidia/nemotron-speech-streaming-en-0.6b · Kyutai STT https://kyutai.org/stt/ · whisper_streaming (LocalAgreement) https://github.com/ufal/whisper_streaming

**VAD / wake word:** Silero VAD (MIT) · ten-vad https://github.com/TEN-framework/ten-vad · openWakeWord (Apache-2.0) · Porcupine free-tier cap https://www.hackster.io/news/picovoice-launches-completely-free-usage-tier-for-offline-voice-recognition-for-up-to-three-users-e1eafbc97bb0

**TTS engines:** Kokoro-82M https://huggingface.co/hexgrad/Kokoro-82M · kokoro-onnx https://github.com/thewh1teagle/kokoro-onnx · Chatterbox (MIT) https://github.com/resemble-ai/chatterbox · Coqui XTTS-v2 license (CPML/non-commercial) https://huggingface.co/coqui/XTTS-v2/blob/main/LICENSE.txt · Piper (GPL-3.0) https://github.com/OHF-Voice/piper1-gpl · F5-TTS https://github.com/SWivid/F5-TTS

**Injection / desktop:** ydotool + wtype https://github.com/atx/wtype · virtual-keyboard protocol https://wayland.app/protocols/virtual-keyboard-unstable-v1 · COSMIC/Smithay protocol gap https://gist.github.com/danielrosehill/d3913d4c8cc69acaf3ee7772771c2f1d · nerd-dictation ydotool notes https://github.com/ideasman42/nerd-dictation/blob/main/readme-ydotool.rst · gtk4-layer-shell https://github.com/wmww/gtk4-layer-shell

**Comparators / patterns:** nerd-dictation https://github.com/ideasman42/nerd-dictation · whisrs https://github.com/y0sif/whisrs · hyprvoice https://github.com/LeonardoTrapani/hyprvoice · WhisperLiveKit https://github.com/QuentinFuxa/WhisperLiveKit

**Audio capture:** sounddevice https://pypi.org/project/sounddevice/ · python-rtmixer https://github.com/spatialaudio/python-rtmixer

**Cloud adapters (roadmap targets):** Deepgram, AssemblyAI, OpenAI audio, ElevenLabs, Google Chirp 3, Azure Speech.
