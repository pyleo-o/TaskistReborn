# -*- coding: utf-8 -*-
"""scrum_service.py — Günlük scrum asistanı."""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from src.repositories.scrum_repository import ScrumRepository


class ScrumService:
    def __init__(self, repo: Optional[ScrumRepository] = None) -> None:
        self._repo = repo or ScrumRepository()

    def bugun_doldurulmali_mi(self, kullanici_id: int, ekip_id: int) -> bool:
        return not self._repo.bugun_kayit_var_mi(int(kullanici_id), int(ekip_id))

    def kaydet(self, kullanici_id: int, ekip_id: int, dun: str, bugun: str, engel: str) -> tuple[bool, str]:
        if not (bugun or "").strip():
            return False, "Bugün ne yapacaksınız alanı zorunludur."
        self._repo.kaydet(int(kullanici_id), int(ekip_id), dun.strip(), bugun.strip(), engel.strip())
        return True, "Günlük scrum kaydedildi."

    def ekip_ozeti(self, ekip_id: int, tarih: Optional[str] = None) -> list[dict[str, Any]]:
        return self._repo.ekip_gunluk_ozet(int(ekip_id), tarih or date.today().isoformat())
