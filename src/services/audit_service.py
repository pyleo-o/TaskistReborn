# -*- coding: utf-8 -*-
"""audit_service.py — Merkezi işlem günlüğü kaydı."""

from __future__ import annotations

from typing import Optional

from src.repositories.tasks_repository import TasksRepository


class AuditService:
    """Islem_Loglari tek giriş noktası."""

    def __init__(self, repo: Optional[TasksRepository] = None) -> None:
        self._repo = repo or TasksRepository()

    def log_islem(
        self,
        islem_tipi: str,
        detay: str,
        kullanici_id: Optional[int] = None,
        ekip_id: Optional[int] = None,
        gorev_id: Optional[int] = None,
        sure_saniye: Optional[int] = None,
    ) -> None:
        self._repo.islem_log_ekle(
            kullanici_id=kullanici_id,
            ekip_id=ekip_id,
            gorev_id=gorev_id,
            islem_tipi=islem_tipi,
            detay=detay,
            sure_saniye=sure_saniye,
        )

    def ekip_loglarini_listele(self, ekip_id: int, limit: int = 200) -> list:
        return self._repo.ekip_islem_loglari(int(ekip_id), limit=limit)
