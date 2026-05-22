# -*- coding: utf-8 -*-
"""
developer_task_service.py — Geliştirici paneli görev akışı (kod yükleme / tarayıcı).
"""

from __future__ import annotations

from typing import Any, Optional, Tuple

from src.services.audit_service import AuditService
from src.services.code_scanner_service import CodeScannerService
from src.repositories.tasks_repository import TasksRepository
import src.config as config


class DeveloperTaskService:
    """Ekip bağlamında geliştirici görev işlemleri."""

    def __init__(
        self,
        ekip_id: int,
        repo: Optional[TasksRepository] = None,
        scanner: Optional[CodeScannerService] = None,
        audit: Optional[AuditService] = None,
    ) -> None:
        self._ekip_id = int(ekip_id)
        self._repo = repo or TasksRepository()
        self._scanner = scanner or CodeScannerService()
        self._audit = audit or AuditService()

    def bana_atanan_acik_gorevler(self, kullanici_id: int) -> list[dict[str, Any]]:
        try:
            return self._repo.gelistirici_acik_gorevler(self._ekip_id, int(kullanici_id))
        except Exception as ex:
            raise RuntimeError(f"Görev listesi alınamadı: {ex}") from ex

    def gorev_ustlen(self, gorev_id: int, kullanici_id: int) -> Tuple[bool, str]:
        try:
            self._repo.gorev_ustlen(int(gorev_id), int(kullanici_id))
            self._audit.log_islem(
                "GOREV_USTLENILDI",
                "Görev üstlenildi; durum Kodlanıyor.",
                kullanici_id=int(kullanici_id),
                ekip_id=self._ekip_id,
                gorev_id=int(gorev_id),
            )
            return True, "Görev üstlenildi. Kodlamaya başlayabilirsiniz."
        except (PermissionError, ValueError) as ex:
            return False, str(ex)
        except Exception as ex:
            return False, f"İşlem hatası: {ex}"

    def kod_yukle_ve_teste_gonder(
        self,
        gorev_id: int,
        kullanici_id: int,
        kod_metni: str,
        zorla_test: bool = False,
    ) -> Tuple[bool, str, bool]:
        """
        Returns:
            (basarili, mesaj, teste_gitti_mi)
        """
        if not (kod_metni or "").strip():
            return False, "Kod alanı boş bırakılamaz.", False

        tarama = self._scanner.tara(kod_metni)

        if zorla_test:
            try:
                self._repo.gorev_teste_zorla(
                    int(gorev_id), int(kullanici_id), kod_metni, tarama.ozet
                )
                self._audit.log_islem(
                    "KOD_TESTE_ZORLA",
                    "Tarayıcı uyarıları yoksayılarak teste gönderildi.",
                    kullanici_id=int(kullanici_id),
                    ekip_id=self._ekip_id,
                    gorev_id=int(gorev_id),
                )
                return True, "Görev test aşamasına alındı (manuel gönderim).", True
            except Exception as ex:
                return False, str(ex), False

        if not tarama.basarili:
            try:
                self._repo.gorev_tarayici_revizyon(
                    int(gorev_id), int(kullanici_id), kod_metni, tarama.ozet
                )
                self._audit.log_islem(
                    "KOD_TARAYICI_REVIZE",
                    tarama.ozet[:500],
                    kullanici_id=int(kullanici_id),
                    ekip_id=self._ekip_id,
                    gorev_id=int(gorev_id),
                )
                return False, tarama.ozet, False
            except Exception as ex:
                return False, str(ex), False

        try:
            self._repo.gorev_kodu_yukle_ve_teste_gonder(
                int(gorev_id), int(kullanici_id), kod_metni, tarama.ozet
            )
            self._audit.log_islem(
                "KOD_TESTE_GONDERILDI",
                tarama.ozet,
                kullanici_id=int(kullanici_id),
                ekip_id=self._ekip_id,
                gorev_id=int(gorev_id),
            )
            return True, tarama.ozet + "\nGörev tester onayına gönderildi.", True
        except (PermissionError, ValueError) as ex:
            return False, str(ex), False
        except Exception as ex:
            return False, f"Kayıt hatası: {ex}", False
