# -*- coding: utf-8 -*-
"""notification_service.py — Uygulama içi bildirim + e-posta simülasyonu."""

from __future__ import annotations

import os
from typing import Any, Optional

import src.config as config
from src.repositories.notifications_repository import NotificationsRepository

_LOG_DIZINI = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
_EMAIL_LOG = os.path.join(_LOG_DIZINI, "email_simulation.log")


class NotificationService:
    def __init__(self, repo: Optional[NotificationsRepository] = None) -> None:
        self._repo = repo or NotificationsRepository()

    def _email_simule(self, kullanici_id: int, baslik: str, mesaj: str) -> None:
        os.makedirs(_LOG_DIZINI, exist_ok=True)
        satir = f"[SIM] kullanici={kullanici_id} | {baslik} | {mesaj}\n"
        try:
            with open(_EMAIL_LOG, "a", encoding="utf-8") as f:
                f.write(satir)
        except Exception:
            pass

    def bildir(
        self,
        kullanici_id: int,
        baslik: str,
        mesaj: str,
        tip: str = config.BILDIRIM_TIP_GENEL,
        ekip_id: Optional[int] = None,
        ilgili_kullanici_id: Optional[int] = None,
        ilgili_kayit_id: Optional[int] = None,
    ) -> int:
        bid = self._repo.ekle(
            int(kullanici_id),
            baslik,
            mesaj,
            tip,
            ekip_id,
            ilgili_kullanici_id,
            ilgili_kayit_id,
        )
        self._email_simule(int(kullanici_id), baslik, mesaj)
        return bid

    def liste(self, kullanici_id: int) -> list[dict[str, Any]]:
        return self._repo.kullanici_bildirimleri(int(kullanici_id))

    def okunmamis(self, kullanici_id: int) -> int:
        return self._repo.okunmamis_sayisi(int(kullanici_id))

    def okundu(self, bildirim_id: int, kullanici_id: int) -> None:
        self._repo.okundu_isaretle(int(bildirim_id), int(kullanici_id))

    def tumunu_okundu(self, kullanici_id: int) -> None:
        self._repo.tumunu_okundu(int(kullanici_id))
