"""Layered, validated configuration (KTD6).

Precedence: built-in defaults < TOML file (XDG) < `TTSTT_*` env vars < explicit CLI
overrides. Each layer is a nested `{section: {key: value}}` dict; the four layers are
merged with per-key provenance tracked (`resolve()`), then validated as a whole against
the `Config` pydantic model. Hand-rolling the merge (rather than pydantic-settings) is
deliberate: `ttstt config show` needs to report which layer produced each effective
value, which pydantic-settings' merge does not expose.

Env mapping: `TTSTT_<SECTION>__<KEY>` (double underscore separates section from key),
e.g. `TTSTT_STT__MODEL=small` sets `stt.model`.

Public API for other units: `load_config()`.
"""

from __future__ import annotations

import json
import os
import tomllib
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, ValidationError

_ENV_PREFIX = "TTSTT_"


class ConfigError(Exception):
    """Raised for any config problem with an actionable, user-facing message."""


class SttConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str = "base"
    device: Literal["auto", "cpu", "cuda"] = "auto"
    language: str | None = None
    compute_type: str = "int8"


class InjectConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: Literal["auto", "wtype", "clipboard", "ydotool"] = "auto"
    sensitive: bool = False


class ActivationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["toggle"] = "toggle"


class AudioConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_device: str | None = None
    sample_rate: int = 16000


class RuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    log_level: str = "INFO"


class Config(BaseModel):
    """The effective, validated ttstt configuration."""

    model_config = ConfigDict(extra="forbid")

    stt: SttConfig = SttConfig()
    inject: InjectConfig = InjectConfig()
    activation: ActivationConfig = ActivationConfig()
    audio: AudioConfig = AudioConfig()
    runtime: RuntimeConfig = RuntimeConfig()


# Single source of truth for the "default" layer: derived from the model itself so
# defaults are never declared twice.
_DEFAULTS_NESTED: dict[str, dict[str, Any]] = Config().model_dump()


def default_config_path() -> Path:
    """The XDG-based config file path: `$XDG_CONFIG_HOME/ttstt/config.toml`, falling
    back to `~/.config/ttstt/config.toml`."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "ttstt" / "config.toml"


def _flatten(nested: dict[str, dict[str, Any]]) -> dict[tuple[str, str], Any]:
    return {
        (section, key): value
        for section, keys in nested.items()
        for key, value in keys.items()
    }


def _format_validation_error(exc: ValidationError) -> str:
    lines = ["invalid configuration:"]
    for error in exc.errors():
        loc = ".".join(str(part) for part in error["loc"])
        lines.append(f"  {loc}: {error['msg']}")
    return "\n".join(lines)


def _merge_and_validate(
    *layers: tuple[str, dict[str, dict[str, Any]]],
) -> tuple[Config, dict[str, str]]:
    values: dict[tuple[str, str], Any] = dict(_flatten(_DEFAULTS_NESTED))
    sources: dict[tuple[str, str], str] = dict.fromkeys(values, "default")

    for layer_name, layer_nested in layers:
        for key, value in _flatten(layer_nested).items():
            values[key] = value
            sources[key] = layer_name

    merged_nested: dict[str, dict[str, Any]] = {}
    for (section, key), value in values.items():
        merged_nested.setdefault(section, {})[key] = value

    try:
        config = Config.model_validate(merged_nested)
    except ValidationError as exc:
        raise ConfigError(_format_validation_error(exc)) from exc

    source_labels = {f"{section}.{key}": src for (section, key), src in sources.items()}
    return config, source_labels


def _read_toml_file(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"failed to parse config file {path}: {exc}") from exc
    for key, value in data.items():
        if not isinstance(value, dict):
            raise ConfigError(
                f"config file {path}: top-level key '{key}' must be a table "
                f"(e.g. [{key}]), not a plain value"
            )
    return data


def _read_env() -> dict[str, dict[str, str]]:
    nested: dict[str, dict[str, str]] = {}
    for name, raw_value in os.environ.items():
        if not name.startswith(_ENV_PREFIX):
            continue
        remainder = name[len(_ENV_PREFIX) :]
        if "__" not in remainder:
            continue
        section, key = remainder.split("__", 1)
        nested.setdefault(section.lower(), {})[key.lower()] = raw_value
    return nested


def _dotted_to_nested(overrides: dict[str, Any]) -> dict[str, dict[str, Any]]:
    nested: dict[str, dict[str, Any]] = {}
    for dotted_key, value in overrides.items():
        section, key = _split_dotted(dotted_key)
        nested.setdefault(section, {})[key] = value
    return nested


def _split_dotted(dotted_key: str) -> tuple[str, str]:
    if "." not in dotted_key:
        raise ConfigError(f"invalid config key '{dotted_key}': expected '<section>.<key>'")
    section, key = dotted_key.split(".", 1)
    return section, key


def resolve(
    cli_overrides: dict[str, Any] | None = None,
    config_path: Path | None = None,
) -> tuple[Config, dict[str, str]]:
    """Merge defaults < file < env < cli, validate, and return (config, sources).

    `sources` maps each dotted key (e.g. "stt.model") to the layer that set its
    effective value: "default", "file", "env", or "cli".
    """
    path = config_path or default_config_path()
    file_nested = _read_toml_file(path)
    env_nested = _read_env()
    cli_nested = _dotted_to_nested(cli_overrides or {})
    return _merge_and_validate(("file", file_nested), ("env", env_nested), ("cli", cli_nested))


def load_config(
    cli_overrides: dict[str, Any] | None = None,
    config_path: Path | None = None,
) -> Config:
    """Public entry point for other units (daemon/audio/stt/inject/onboarding).

    Returns the effective, validated config. Raises `ConfigError` with an
    actionable message on a malformed file, unknown keys, or invalid values.
    """
    config, _sources = resolve(cli_overrides=cli_overrides, config_path=config_path)
    return config


def get_config_value(dotted_key: str, config_path: Path | None = None) -> Any:
    """Look up the effective value of a dotted key (e.g. "stt.model")."""
    config, _sources = resolve(config_path=config_path)
    section, key = _split_dotted(dotted_key)
    section_model = getattr(config, section, None)
    if section_model is None or not hasattr(section_model, key):
        raise ConfigError(f"unknown config key: {dotted_key}")
    return getattr(section_model, key)


def _toml_literal(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return json.dumps(str(value))


def _write_toml_file(path: Path, nested: dict[str, dict[str, Any]]) -> None:
    lines: list[str] = []
    for section in sorted(nested):
        keys = {k: v for k, v in nested[section].items() if v is not None}
        if not keys:
            continue
        lines.append(f"[{section}]")
        for key in sorted(keys):
            lines.append(f"{key} = {_toml_literal(keys[key])}")
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n")


def set_config_value(dotted_key: str, raw_value: str, config_path: Path | None = None) -> None:
    """Write a single dotted key into the config file, preserving other keys.

    Validates the resulting file layer (against defaults, ignoring the current
    env/cli) before writing, so an invalid `set` fails fast without touching disk.
    """
    path = config_path or default_config_path()
    section, key = _split_dotted(dotted_key)
    file_nested = _read_toml_file(path)
    file_nested.setdefault(section, {})[key] = raw_value

    # Validate with the RAW string — pydantic's lax mode coerces "8000"->int and
    # "true"->bool exactly where the target field demands it (same as the env-var
    # path) and leaves str fields alone (lax mode never coerces int->str, so
    # pre-guessing the type here would wrongly reject e.g. "2" for a str field).
    # On success, write the *validated* value so the TOML stays cleanly typed.
    config, _sources = _merge_and_validate(("file", file_nested))
    file_nested[section][key] = getattr(getattr(config, section), key)

    path.parent.mkdir(parents=True, exist_ok=True)
    _write_toml_file(path, file_nested)
