"""Tests for the layered ttstt config system (U2).

Covers the brief's six scenarios:
- AE6 precedence: file sets a value, env overrides it -> effective is the env value.
- CLI overrides both env and file for the same key.
- Missing config file -> defaults load without error, source is "default".
- Invalid value -> actionable error, non-zero exit (not a raw traceback).
- `config show` reports the correct source label (default/file/env/cli) per key.
- Unknown/extra keys in the TOML are rejected with an actionable message.

Env/XDG isolation: every test runs through the `_isolated_env` autouse fixture, which
points XDG_CONFIG_HOME at a tmp_path and strips any TTSTT_* vars from the real
environment, so these tests never read the developer's actual config.
"""

import os

import pytest

from ttstt.cli import main
from ttstt.config import (
    Config,
    ConfigError,
    default_config_path,
    get_config_value,
    load_config,
    resolve,
    set_config_value,
)


@pytest.fixture(autouse=True)
def _isolated_env(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    for name in list(os.environ):
        if name.startswith("TTSTT_"):
            monkeypatch.delenv(name, raising=False)
    yield


def _write_config(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


# --- default_config_path (XDG) -------------------------------------------------


def test_default_config_path_uses_xdg_config_home(tmp_path):
    assert default_config_path() == tmp_path / "ttstt" / "config.toml"


def test_default_config_path_falls_back_to_home_config(tmp_path, monkeypatch):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setattr("ttstt.config.Path.home", lambda: tmp_path)
    assert default_config_path() == tmp_path / ".config" / "ttstt" / "config.toml"


# --- missing file -> defaults ---------------------------------------------------


def test_missing_config_file_loads_defaults_without_error():
    path = default_config_path()
    assert not path.exists()
    config = load_config(config_path=path)
    assert config.stt.model == "base"
    assert config.stt.device == "auto"
    assert config.inject.method == "auto"
    assert config.activation.mode == "toggle"


def test_missing_config_file_source_is_default():
    path = default_config_path()
    _config, sources = resolve(config_path=path)
    assert sources["stt.model"] == "default"
    assert sources["inject.method"] == "default"


# --- AE6: file < env precedence --------------------------------------------------


def test_ae6_env_overrides_file(tmp_path, monkeypatch):
    path = tmp_path / "ttstt" / "config.toml"
    _write_config(path, '[stt]\nmodel = "base"\n')
    monkeypatch.setenv("TTSTT_STT__MODEL", "small")

    config = load_config(config_path=path)

    assert config.stt.model == "small"


def test_ae6_source_labels_default_file_env(tmp_path, monkeypatch):
    path = tmp_path / "ttstt" / "config.toml"
    _write_config(path, '[stt]\nmodel = "base"\n')
    monkeypatch.setenv("TTSTT_STT__MODEL", "small")

    _config, sources = resolve(config_path=path)

    assert sources["stt.model"] == "env"
    # untouched key from an untouched section stays "default".
    assert sources["activation.mode"] == "default"


# --- CLI overrides both env and file ---------------------------------------------


def test_cli_overrides_env_and_file(tmp_path, monkeypatch):
    path = tmp_path / "ttstt" / "config.toml"
    _write_config(path, '[stt]\nmodel = "base"\n')
    monkeypatch.setenv("TTSTT_STT__MODEL", "small")

    config, sources = resolve(cli_overrides={"stt.model": "large-v3"}, config_path=path)

    assert config.stt.model == "large-v3"
    assert sources["stt.model"] == "cli"


# --- invalid value -> actionable error -------------------------------------------


def test_invalid_device_value_raises_actionable_config_error(tmp_path):
    path = tmp_path / "ttstt" / "config.toml"
    _write_config(path, '[stt]\ndevice = "banana"\n')

    with pytest.raises(ConfigError) as excinfo:
        load_config(config_path=path)

    message = str(excinfo.value)
    assert "stt.device" in message


def test_config_show_cli_reports_nonzero_and_no_traceback_on_invalid_value(
    tmp_path, capsys
):
    path = default_config_path()
    _write_config(path, '[stt]\ndevice = "banana"\n')

    exit_code = main(["config", "show"])

    assert exit_code != 0
    err = capsys.readouterr().err
    assert "Traceback" not in err
    assert "stt.device" in err


# --- unknown/extra keys rejected -------------------------------------------------


def test_unknown_section_rejected(tmp_path):
    path = tmp_path / "ttstt" / "config.toml"
    _write_config(path, '[bogus]\nfoo = "bar"\n')

    with pytest.raises(ConfigError):
        load_config(config_path=path)


def test_unknown_key_in_known_section_rejected(tmp_path):
    path = tmp_path / "ttstt" / "config.toml"
    _write_config(path, '[stt]\nmodel = "base"\nbogus_key = "x"\n')

    with pytest.raises(ConfigError):
        load_config(config_path=path)


# --- config.py public API used by other units ------------------------------------


def test_load_config_returns_config_instance(tmp_path):
    path = tmp_path / "ttstt" / "config.toml"
    config = load_config(config_path=path)
    assert isinstance(config, Config)


def test_get_config_value(tmp_path):
    path = tmp_path / "ttstt" / "config.toml"
    _write_config(path, '[stt]\nmodel = "small"\n')
    assert get_config_value("stt.model", config_path=path) == "small"


def test_set_config_value_writes_and_preserves_other_keys(tmp_path):
    path = tmp_path / "ttstt" / "config.toml"
    _write_config(path, '[stt]\nmodel = "base"\ndevice = "cuda"\n')

    set_config_value("stt.model", "small", config_path=path)

    config = load_config(config_path=path)
    assert config.stt.model == "small"
    assert config.stt.device == "cuda"  # preserved, not clobbered


def test_set_config_value_creates_parent_dirs(tmp_path):
    path = tmp_path / "nested" / "dir" / "config.toml"
    assert not path.parent.exists()

    set_config_value("stt.model", "small", config_path=path)

    assert path.exists()
    assert load_config(config_path=path).stt.model == "small"


def test_set_config_value_rejects_invalid_value(tmp_path):
    path = tmp_path / "ttstt" / "config.toml"
    with pytest.raises(ConfigError):
        set_config_value("stt.device", "banana", config_path=path)
    assert not path.exists()


def test_set_numeric_looking_value_on_string_field(tmp_path):
    """sounddevice commonly addresses devices by integer index, so "2" is a realistic
    value for the str-typed audio.input_device — it must not be pre-coerced to int and
    then rejected by the str field."""
    path = tmp_path / "ttstt" / "config.toml"

    set_config_value("audio.input_device", "2", config_path=path)

    assert load_config(config_path=path).audio.input_device == "2"
    assert 'input_device = "2"' in path.read_text()


def test_set_int_field_writes_typed_toml(tmp_path):
    path = tmp_path / "ttstt" / "config.toml"

    set_config_value("audio.sample_rate", "8000", config_path=path)

    assert load_config(config_path=path).audio.sample_rate == 8000
    assert "sample_rate = 8000" in path.read_text()  # bare int, not a quoted string


def test_set_bool_field_writes_typed_toml(tmp_path):
    path = tmp_path / "ttstt" / "config.toml"

    set_config_value("inject.sensitive", "true", config_path=path)

    assert load_config(config_path=path).inject.sensitive is True
    assert "sensitive = true" in path.read_text()  # bare bool, not a quoted string


# --- CLI subcommands --------------------------------------------------------------


def test_cli_config_path_prints_path(tmp_path, capsys):
    exit_code = main(["config", "path"])
    assert exit_code == 0
    out = capsys.readouterr().out.strip()
    assert out == str(tmp_path / "ttstt" / "config.toml")


def test_cli_config_show_lists_keys_and_sources(capsys):
    exit_code = main(["config", "show"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "stt.model" in out
    assert "source: default" in out


def test_cli_config_get_prints_value(monkeypatch, tmp_path, capsys):
    path = tmp_path / "ttstt" / "config.toml"
    _write_config(path, '[stt]\nmodel = "small"\n')

    exit_code = main(["config", "get", "stt.model"])

    assert exit_code == 0
    assert capsys.readouterr().out.strip() == "small"


def test_cli_config_set_then_get_roundtrip(capsys):
    exit_code = main(["config", "set", "stt.model", "small"])
    assert exit_code == 0
    capsys.readouterr()

    exit_code = main(["config", "get", "stt.model"])
    assert exit_code == 0
    assert capsys.readouterr().out.strip() == "small"


def test_cli_config_get_unknown_key_is_actionable_not_traceback(capsys):
    exit_code = main(["config", "get", "stt.nonexistent"])
    assert exit_code != 0
    err = capsys.readouterr().err
    assert "Traceback" not in err
    assert "stt.nonexistent" in err


def test_cli_config_set_unwritable_dir_is_actionable_not_traceback(tmp_path, capsys):
    """A permission error writing the config file must surface as an actionable
    message + non-zero exit, not a raw OSError traceback."""
    config_dir = tmp_path / "ttstt"
    config_dir.mkdir()
    config_dir.chmod(0o555)  # read+execute only: file creation inside will fail
    try:
        exit_code = main(["config", "set", "stt.model", "small"])
    finally:
        config_dir.chmod(0o755)  # let pytest clean tmp_path up

    assert exit_code != 0
    err = capsys.readouterr().err
    assert "Traceback" not in err
    assert "config.toml" in err
