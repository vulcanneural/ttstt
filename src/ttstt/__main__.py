"""Enables `python -m ttstt`, equivalent to the `ttstt` console script."""

from ttstt.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
