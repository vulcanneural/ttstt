"""ttstt command-line interface.

An `argparse` command tree (no click/typer — see CONTRIBUTING.md's minimal-dependencies
rule). Each subcommand is wired to a handler now so the tree is stable; most handlers are
stubs until the unit that owns them lands. `--help` and `--version` always work; every
other stub prints a clear message and exits non-zero rather than silently doing nothing.
"""

import argparse
import sys
from collections.abc import Sequence
from importlib.metadata import PackageNotFoundError, version

from ttstt.config import (
    ConfigError,
    default_config_path,
    get_config_value,
    resolve,
    set_config_value,
)

PROG = "ttstt"

try:
    __version__ = version("ttstt")
except PackageNotFoundError:  # pragma: no cover - only hit when running uninstalled
    __version__ = "0.0.0+unknown"


def _stub(unit: str):
    """Build a handler for a command not yet implemented by any landed unit."""

    def handler(_args: argparse.Namespace) -> int:
        print(f"not yet implemented: lands in {unit}", file=sys.stderr)
        return 1

    return handler


def _roadmap_stub(_args: argparse.Namespace) -> int:
    """Handler for commands that are roadmap-only (not part of the v1 slice)."""
    print("not yet implemented (roadmap)", file=sys.stderr)
    return 1


def _format_config_value(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _config_show(_args: argparse.Namespace) -> int:
    try:
        config, sources = resolve()
    except ConfigError as exc:
        print(exc, file=sys.stderr)
        return 1
    for section, keys in config.model_dump().items():
        for key, value in keys.items():
            dotted = f"{section}.{key}"
            print(f"{dotted} = {_format_config_value(value)}  (source: {sources[dotted]})")
    return 0


def _config_get(args: argparse.Namespace) -> int:
    try:
        value = get_config_value(args.key)
    except ConfigError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(_format_config_value(value))
    return 0


def _config_set(args: argparse.Namespace) -> int:
    try:
        set_config_value(args.key, args.value)
    except ConfigError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


def _config_path(_args: argparse.Namespace) -> int:
    print(default_config_path())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Local-first, modular speech-to-text and text-to-speech toolkit.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    toggle = subparsers.add_parser(
        "toggle", help="Toggle dictation listening: start on the first press, stop on the next."
    )
    toggle.set_defaults(func=_stub("U7"))

    daemon = subparsers.add_parser(
        "daemon", help="Run the ttstt background daemon (control socket + capture/STT/inject loop)."
    )
    daemon.set_defaults(func=_stub("U7"))

    onboard = subparsers.add_parser(
        "onboard",
        help="First-run setup: check dependencies, fetch the default model, write config.",
    )
    onboard.set_defaults(func=_stub("U8"))

    config = subparsers.add_parser(
        "config", help="Inspect or edit the layered configuration (get/set/path/show)."
    )
    config_sub = config.add_subparsers(dest="config_command", required=True)

    config_show = config_sub.add_parser(
        "show", help="Print the effective merged config, with the source of each value."
    )
    config_show.set_defaults(func=_config_show)

    config_get = config_sub.add_parser("get", help="Print the value of a dotted config key.")
    config_get.add_argument("key", help="Dotted key, e.g. stt.model")
    config_get.set_defaults(func=_config_get)

    config_set = config_sub.add_parser(
        "set", help="Set a dotted config key in the config file (other keys are preserved)."
    )
    config_set.add_argument("key", help="Dotted key, e.g. stt.model")
    config_set.add_argument("value", help="New value")
    config_set.set_defaults(func=_config_set)

    config_path_cmd = config_sub.add_parser("path", help="Print the config file path.")
    config_path_cmd.set_defaults(func=_config_path)

    ptt = subparsers.add_parser(
        "ptt", help="[roadmap] True hold push-to-talk activation (evdev key down/up)."
    )
    ptt.set_defaults(func=_roadmap_stub)

    say = subparsers.add_parser(
        "say", help="[roadmap] Speak text (or stdin) aloud via local text-to-speech."
    )
    say.set_defaults(func=_roadmap_stub)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
