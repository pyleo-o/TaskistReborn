# -*- coding: utf-8 -*-
"""
tester_task_service.py — Tester paneli: testteki görevleri onaylama veya revizyona gönderme.

Onay: görev Tamamlandı + Islem_Loglari'na atama–bitiş arası süre (saniye) yazılır.
Revize: kritiklik matrisi revize_kritikligi alanına işlenir, durum Revizyon olur.
"""

from __future__ import annotations

from typing import Any, Optional, Tuple

import src.config as config
from src.repositories.tasks_repository import TasksRepository


class TesterTaskService:
    """Ekip bağlamında tester görev işlemleri."""

    def __init__(self, ekip_id: int, repo: Optional[TasksRepository] = None) -> None:
        self._ekip_id = int(ekip_id)
        self._repo = repo or TasksRepository()

    def testteki_gorevler(self) -> list[dict[str, Any]]:
        """Sol panel listesi."""
        try:
            return self._repo.ekip_testteki_gorevler(self._ekip_id)
        except Exception as ex:
            raise RuntimeError(f"Test görevleri alınamadı: {ex}") from ex

    def gorev_onayla(self, gorev_id: int, tester_kullanici_id: int) -> Tuple[bool, str, int]:
        """
        Returns:
            (başarılı, mesaj, süre_saniye) — süre log tablosuna yazılan değerdir.
        """
        try:
            sure = self._repo.gorev_onayla_tamamla(
                int(gorev_id),
                int(tester_kullanici_id),
                self._ekip_id,
            )
            return True, "Görev onaylandı ve tamamlandı olarak işaretlendi.", int(sure)
        except ValueError as ve:
            return False, str(ve), 0
        except Exception as ex:
            return False, f"Veritabanı hatası: {ex}", 0

    def gorev_revize_iste(self, gorev_id: int, tester_kullanici_id: int, matris_seviyesi: str) -> Tuple[bool, str]:
        """Kritiklik matrisinden gelen seviye ile revizyon kaydı."""
        if matris_seviyesi not in config.KRITIKLIK_SECENEKLERI:
            return False, "Geçersiz kritiklik seviyesi."
        try:
            self._repo.gorev_revizeye_gonder(
                int(gorev_id),
                int(tester_kullanici_id),
                self._ekip_id,
                matris_seviyesi,
            )
        except ValueError as ve:
            return False, str(ve)
        except Exception as ex:
            return False, str(ex)
        return True, "Görev yazılımcıya revizyon için iade edildi."
