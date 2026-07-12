"""Tests for the ttstt CLI command tree (argparse wiring only; no domain logic yet).

Covers U1's scoped test scenarios:
- `ttstt --help` exits 0 and lists the command tree.
- `ttstt --version` prints the version from package metadata.
- Stub commands (toggle, daemon, onboard) exit non-zero with a clear
  "not yet implemented: lands in U<n>" message.
- Roadmap stubs (ptt, say) exit non-zero with a "not yet implemented (roadmap)" message.

`config` is implemented (U2, see test_config.py) and is no longer a stub.
"""

import subprocess
import sys
from importlib.metadata import version

import pytest

from ttstt.cli import main

COMMANDS = ("toggle", "daemon", "onboard", "config", "ptt", "say")


def test_help_exits_zero_and_lists_command_tree(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    for command in COMMANDS:
        assert command in out


def test_version_prints_package_metadata_version(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    assert version("ttstt") in out


@pytest.mark.parametrize(
    ("command", "unit"),
    [
        ("toggle", "U7"),
        ("daemon", "U7"),
        ("onboard", "U8"),
    ],
)
def test_stub_commands_exit_nonzero_with_unit_reference(capsys, command, unit):
    exit_code = main([command])
    assert exit_code != 0
    err = capsys.readouterr().err
    assert "not yet implemented" in err
    assert unit in err


@pytest.mark.parametrize("command", ["ptt", "say"])
def test_roadmap_stubs_exit_nonzero_with_roadmap_message(capsys, command):
    exit_code = main([command])
    assert exit_code != 0
    err = capsys.readouterr().err
    assert "not yet implemented (roadmap)" in err


def test_console_entry_point_help_via_module_invocation():
    """End-to-end smoke test: `python -m ttstt --help` really runs and exits 0."""
    result = subprocess.run(
        [sys.executable, "-m", "ttstt", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    for command in COMMANDS:
        assert command in result.stdout
