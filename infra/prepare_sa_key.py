#!/usr/bin/env python3
"""Создаёт authorized_key.json из секрета GitHub Actions (JSON или base64)."""

from __future__ import annotations

import base64
import json
import os
import re
import sys
from typing import Callable

REQUIRED = frozenset({"id", "service_account_id", "private_key"})
OUTPUT = "authorized_key.json"


def _normalize(text: str) -> str:
    text = text.strip().lstrip("\ufeff")
    return (
        text.replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
    )


def _validate_key(obj: object) -> dict:
    if isinstance(obj, str):
        obj = json.loads(obj)
    if not isinstance(obj, dict):
        raise ValueError("ожидается JSON-объект authorized_key.json")
    missing = REQUIRED - obj.keys()
    if missing:
        raise ValueError("нет обязательных полей: " + ", ".join(sorted(missing)))
    if not str(obj.get("private_key", "")).strip():
        raise ValueError("поле private_key пустое")
    return obj


def _try_json(text: str) -> dict | None:
    try:
        return _validate_key(json.loads(text))
    except (json.JSONDecodeError, ValueError, TypeError):
        return None


def _try_base64_json(text: str) -> dict | None:
    try:
        blob = re.sub(r"[^A-Za-z0-9+/=_-]", "", text)
        pad = (-len(blob)) % 4
        decoded = base64.b64decode(blob + "=" * pad, validate=False).decode("utf-8")
        return _validate_key(json.loads(decoded))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError, TypeError):
        return None


def _diagnose(raw: str) -> None:
    """Безопасная подсказка в лог CI (секрет не выводится)."""
    preview = raw[:20].replace("\n", "\\n").replace("\r", "\\r")
    print("::group::Диагностика секрета (значение не показывается)")
    print(f"  длина: {len(raw)} символов")
    print(f"  строк: {raw.count(chr(10)) + 1}")
    print(f"  начинается с '{{': {raw.startswith('{')}")
    print(f"  начинается с '\"': {raw.startswith('\"')}")
    print(f"  похоже на base64: {bool(re.fullmatch(r'[A-Za-z0-9+/=\s-]+', raw[:200]))}")
    print(f"  первые символы (маска): {preview!r}...")
    if raw.startswith("***"):
        print(
            "  ⚠ Похоже на маску GitHub (***) — в секрет попал не ключ, "
            "а замаскированный вывод из лога."
        )
    if re.match(r"^YCA[A-Za-z0-9]+$", raw.split()[0] if raw.split() else ""):
        print(
            "  ⚠ Похоже на статический ключ доступа (YCA...), а не JSON ключа SA."
        )
    if raw.startswith("AQVN"):
        print("  ⚠ Похоже на IAM-токен, а не на authorized_key.json.")
    if "BEGIN PRIVATE KEY" in raw and not raw.strip().startswith("{"):
        print(
            "  ⚠ Есть PEM, но нет JSON-обёртки — нужен весь файл authorized_key.json."
        )
    print("::endgroup::")


def parse_sa_key(raw: str) -> tuple[dict, str]:
    raw = _normalize(raw)
    if not raw:
        raise ValueError("пустое значение")

    attempts: list[tuple[str, Callable[[str], dict | None]]] = [
        ("JSON", _try_json),
        ("base64(JSON)", _try_base64_json),
    ]
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        inner = raw[1:-1]
        attempts.extend(
            [
                (f"JSON в {raw[0]!r}", lambda t: _try_json(inner)),
                (f"base64(JSON) в {raw[0]!r}", lambda t: _try_base64_json(inner)),
            ]
        )

    for label, parser in attempts:
        key = parser(raw)
        if key is not None:
            return key, label

    raise ValueError("не удалось разобрать ключ")


def write_key(obj: dict, path: str = OUTPUT) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False)


def main() -> int:
    raw = os.environ.get("SA_KEY", "")
    for name in (
        "YC_SERVICE_ACCOUNT_KEY_FILE",
        "YC_SERVICE_ACCOUNT_KEY",
        "SA_KEY",
    ):
        if not raw:
            raw = os.environ.get(name, "")

    try:
        key, label = parse_sa_key(raw)
    except ValueError as exc:
        _diagnose(_normalize(raw))
        print(f"::error::{exc}", file=sys.stderr)
        print(
            "::error::Обновите секрет одной из команд (из корня репозитория, "
            "где лежит authorized_key.json):\n"
            "  gh secret set YC_SERVICE_ACCOUNT_KEY_FILE --body-file authorized_key.json\n"
            "  # или одной строкой base64:\n"
            "  gh secret set YC_SERVICE_ACCOUNT_KEY_FILE --body \"$(base64 -w0 authorized_key.json)\"",
            file=sys.stderr,
        )
        return 1

    write_key(key)
    print(f"authorized_key.json создан (формат: {label})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
