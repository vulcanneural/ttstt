"""
U0 feasibility spike (throwaway, no abstractions).

Proves:
  (a) faster-whisper transcribes on this machine's RTX 3070 (CUDA/int8),
      with clean CPU fallback if CUDA path fails.
  (b) wtype can complete the virtual-keyboard protocol handshake with the
      COSMIC/Wayland compositor (WITHOUT injecting any visible text, since
      this is an unattended session and a human may be typing elsewhere).

Run with:
  uv run --with faster-whisper --with 'nvidia-cudnn-cu12>=9,<10' \
      --with nvidia-cublas-cu12 python scratch/spike.py
"""

import glob
import os
import shutil
import subprocess
import sys
import time

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "jfk.wav")


def setup_cuda_ld_library_path():
    """faster-whisper/CTranslate2 on CUDA needs cuDNN 9 + cuBLAS for CUDA 12.
    Locate the nvidia pip wheel lib dirs (installed by `uv run --with`) and
    prepend them to LD_LIBRARY_PATH before ctranslate2/faster-whisper import
    tries to dlopen them."""
    site_packages_globs = glob.glob(
        os.path.join(sys.prefix, "lib", "python3.*", "site-packages")
    ) + glob.glob(
        os.path.join(os.path.dirname(sys.executable), "..", "lib", "python3.*", "site-packages")
    )
    lib_dirs = []
    for sp in site_packages_globs:
        lib_dirs += glob.glob(os.path.join(sp, "nvidia", "*", "lib"))
    lib_dirs = sorted(set(lib_dirs))
    if lib_dirs:
        existing = os.environ.get("LD_LIBRARY_PATH", "")
        os.environ["LD_LIBRARY_PATH"] = ":".join(lib_dirs + ([existing] if existing else []))
    return lib_dirs


def transcribe(device, compute_type):
    from faster_whisper import WhisperModel

    t0 = time.time()
    model = WhisperModel("tiny", device=device, compute_type=compute_type)
    segments, info = model.transcribe(FIXTURE)
    text = " ".join(seg.text for seg in segments).strip()
    elapsed = time.time() - t0
    return text, elapsed


def run_transcription_section():
    print("=" * 70)
    print("TRANSCRIPTION HALF")
    print("=" * 70)

    lib_dirs = setup_cuda_ld_library_path()
    print(f"nvidia lib dirs found for LD_LIBRARY_PATH: {lib_dirs}")

    # --- Attempt 1: CUDA / int8, with CPU fallback on failure ---
    device_used = None
    try:
        print("\n[attempt] device=cuda compute_type=int8 ...")
        text, elapsed = transcribe("cuda", "int8")
        device_used = "cuda"
        print(f"  OK  device_used=cuda  elapsed={elapsed:.2f}s")
    except Exception as e:
        print(f"  FAILED on cuda: {type(e).__name__}: {e}")
        print("[fallback] device=cpu compute_type=int8 ...")
        text, elapsed = transcribe("cpu", "int8")
        device_used = "cpu (fallback from cuda failure)"
        print(f"  OK  device_used=cpu(fallback)  elapsed={elapsed:.2f}s")

    print(f"\ndevice actually used: {device_used}")
    print(f"transcription text: {text!r}")
    print(f"elapsed: {elapsed:.2f}s")
    ok = "country" in text.lower()
    print(f"success check ('country' in transcript, case-insensitive): {ok}")

    # --- Attempt 2: explicit CPU run, to prove fallback path independently ---
    print("\n[explicit] device=cpu compute_type=int8 ...")
    cpu_text, cpu_elapsed = transcribe("cpu", "int8")
    cpu_ok = "country" in cpu_text.lower()
    print(f"  OK  elapsed={cpu_elapsed:.2f}s")
    print(f"  cpu transcription text: {cpu_text!r}")
    print(f"  cpu success check: {cpu_ok}")

    return {
        "device_used": device_used,
        "text": text,
        "elapsed": elapsed,
        "ok": ok,
        "cpu_text": cpu_text,
        "cpu_elapsed": cpu_elapsed,
        "cpu_ok": cpu_ok,
    }


def run_injection_section():
    print("\n" + "=" * 70)
    print("INJECTION HALF (non-intrusive: no visible text is ever typed)")
    print("=" * 70)

    tools = ["wtype", "wl-copy", "wl-paste", "ydotool"]
    availability = {t: shutil.which(t) for t in tools}
    print("\ncapability probe:")
    for t, path in availability.items():
        print(f"  {t}: {'FOUND at ' + path if path else 'NOT FOUND'}")
    print(f"  $WAYLAND_DISPLAY: {os.environ.get('WAYLAND_DISPLAY')!r}")
    print(f"  $XDG_CURRENT_DESKTOP: {os.environ.get('XDG_CURRENT_DESKTOP')!r}")

    wtype_viable = False
    if availability["wtype"]:
        print("\nrunning `wtype ''` (empty string; connects to compositor + creates")
        print("virtual keyboard, types nothing) to validate protocol handshake ...")
        proc = subprocess.run(["wtype", ""], capture_output=True, text=True)
        print(f"  exit code: {proc.returncode}")
        if proc.stdout.strip():
            print(f"  stdout: {proc.stdout.strip()!r}")
        if proc.stderr.strip():
            print(f"  stderr: {proc.stderr.strip()!r}")
        wtype_viable = proc.returncode == 0
        print(f"  wtype virtual-keyboard protocol viable: {wtype_viable}")
    else:
        print("\nwtype not found on PATH; cannot probe protocol handshake.")

    print(
        "\n*** DEFERRED TO HUMAN ***\n"
        "Live end-to-end check (speak into mic, faster-whisper transcribes,\n"
        "wtype injects the resulting text into a focused editor and it visibly\n"
        "appears there) is NOT performed by this spike -- this is an unattended\n"
        "background session with no human at the keyboard/mic, and injecting\n"
        "arbitrary text into whatever window happens to be focused would be\n"
        "unsafe. This check is still owed by a human at Gate 4."
    )

    return {"availability": availability, "wtype_viable": wtype_viable}


def main():
    if not os.path.exists(FIXTURE):
        print(f"FATAL: fixture not found at {FIXTURE}")
        sys.exit(1)

    t_results = run_transcription_section()
    i_results = run_injection_section()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"transcription device used: {t_results['device_used']}")
    print(f"transcription success (cuda/primary attempt): {t_results['ok']}")
    print(f"transcription success (explicit cpu): {t_results['cpu_ok']}")
    print(f"wtype protocol viable: {i_results['wtype_viable']}")
    print(f"injector availability: {i_results['availability']}")


if __name__ == "__main__":
    main()
