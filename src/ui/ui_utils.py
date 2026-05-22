# -*- coding: utf-8 -*-
"""ui_utils.py — Ortak UI yardımcıları."""

from __future__ import annotations

from datetime import date

import src.config as config

_GECIKME_KENAR = "#c0392b"


def due_date_gecikmis_mi(due_date: str | None) -> bool:
    if not due_date or not str(due_date).strip():
        return False
    try:
        d = date.fromisoformat(str(due_date).strip()[:10])
        return d < date.today()
    except ValueError:
        return False


def kart_kenarligi(kritiklik: str, durum: str, due_date: str | None, revize_kritikligi: str | None = None) -> tuple[int, str | tuple]:
    if kritiklik == config.ONCELIK_KRITIK:
        return 2, "#e74c3c"
    if durum == config.DURUM_REVIZYON or revize_kritikligi == config.ONCELIK_KRITIK:
        return 2, "#e74c3c"
    if due_date_gecikmis_mi(due_date):
        return 2, _GECIKME_KENAR
    return 1, ("gray70", "gray32")
