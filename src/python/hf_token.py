"""Hugging Face token resolution for V-SpeechFlow.

Resolution order:
1) Explicit CLI token (e.g. --hf-token)
2) Environment variable HF_TOKEN
3) macOS Keychain generic password (service: HF_V-Speechflow)

The resolved token is cached in-process to avoid repeated Keychain lookups.
"""

from __future__ import annotations

import os
import subprocess
from typing import Optional


KEYCHAIN_SERVICE_NAME = "HF_V-Speechflow"

_cached_token: Optional[str] = None


def _get_token_from_keychain(service_name: str) -> Optional[str]:
    # Best-effort: if not on macOS or `security` is unavailable, just return None.
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", service_name, "-w"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    token = (result.stdout or "").strip()
    return token or None


def get_hf_token(cli_token: Optional[str] = None) -> Optional[str]:
    """Return the Hugging Face token, if available.

    The token is cached after the first successful resolution.
    """
    global _cached_token

    if cli_token:
        _cached_token = cli_token
        return _cached_token

    if _cached_token:
        return _cached_token

    env_token = os.environ.get("HF_TOKEN")
    if env_token:
        _cached_token = env_token
        return _cached_token

    keychain_token = _get_token_from_keychain(KEYCHAIN_SERVICE_NAME)
    if keychain_token:
        _cached_token = keychain_token
        return _cached_token

    return None
