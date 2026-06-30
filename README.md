# TTSTT

**Local-first, modular speech toolkit — speech-to-text and text-to-speech that you actually own.**

TTSTT is a Linux-first voice package that does dictation and speech synthesis locally by
default, with optional cloud backends. It is built to be **readable and hackable** — the
goal is a tool you can open up, understand, and bend to your needs, not a black box.

> Status: early development. The architecture and roadmap live in
> [`docs/plans/`](docs/plans/). Start there.

## What it aims to be

- **Local-first STT** — push-to-talk, recording toggle, voice-activity detection (VAD),
  and passive continuous listening with keyword activation. Streaming by default.
- **Local-first TTS** — a selection of base voices, importable third-party voices, and
  custom voices cloned from your own local samples.
- **Pluggable model backends** — run any model locally on CPU, GPU, or other accelerators;
  connect cloud providers through the same interface.
- **Direct text injection** — type results straight into the focused Wayland/X11 app, with
  clipboard-paste and other methods as fallbacks.
- **Per-user onboarding** — an onboarding script, a default TUI for preferences, an optional
  GUI, and a minimal configurable on-screen display (OSD).

## Design north star

Code style follows Andrej Karpathy's ethos: minimal dependencies, small and explicit over
clever and abstract, hackable single-purpose modules. See the project plan for how this is
applied to a real (non-tutorial) application.

## License

[MIT](LICENSE)
