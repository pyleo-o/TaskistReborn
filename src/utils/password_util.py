# -*- coding: utf-8 -*-
"""password_util.py — Şifre hash (PBKDF2, ek bağımlılık yok)."""

from __future__ import annotations

import hashlib
import os
import secrets

_PREFIX = "pbkdf2_sha256$"


def sifre_hashle(sifre: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", sifre.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"{_PREFIX}{salt}${dk.hex()}"


def sifre_dogrula(sifre: str, kayitli: str) -> bool:
    if not kayitli:
        return False
    if not kayitli.startswith(_PREFIX):
        return kayitli == sifre
    try:
        _, salt, hexd = kayitli.split("$", 2)
        dk = hashlib.pbkdf2_hmac("sha256", sifre.encode("utf-8"), salt.encode("utf-8"), 120_000)
        return secrets.compare_digest(dk.hex(), hexd)
    except Exception:
        return False


def hash_mi(deger: str) -> bool:
    return (deger or "").startswith(_PREFIX)
