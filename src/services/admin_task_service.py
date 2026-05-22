# -*- coding: utf-8 -*-
"""
admin_task_service.py — Yönetici paneli görev oluşturma ve listeleme iş kuralları.

Arayüz doğrudan SQL yazmaz; TasksRepository üzerinden veri erişir.
Tarih ve boş alan doğrulamaları burada toplanır (sunumda tek sorumluluk).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import src.config as config
from src.repositories.tasks_repository import TasksRepository
from src.services.audit_service import AuditService
from src.services.features_service import FeaturesService


@dataclass
class GorevOlusturSonuc:
    """Görev oluşturma işleminin sonucu."""

    basarili: bool
    mesaj: str
    yeni_gorev_id: Optional[int] = None


class AdminTaskService:
    """Belirli bir ekip bağlamında yönetici görev operasyonları."""

    def __init__(
        self,
        ekip_id: int,
        repo: Optional[TasksRepository] = None,
        audit: Optional[AuditService] = None,
        features: Optional[FeaturesService] = None,
    ) -> None:
        self._ekip_id = int(ekip_id)
        self._repo = repo or TasksRepository()
        self._audit = audit or AuditService()
        self._features = features or FeaturesService()

    @property
    def ekip_id(self) -> int:
        return self._ekip_id

    def atanabilir_gelistiriciler(self) -> list[dict[str, Any]]:
        """CTkOptionMenu için: id, etiket üretiminde kullanılacak alanlar."""
        try:
            return self._repo.ekipteki_gelistirici_uyeler(self._ekip_id)
        except Exception as ex:
            raise RuntimeError(f"Geliştirici listesi alınamadı: {ex}") from ex

    def gorev_kartlari(self) -> list[dict[str, Any]]:
        """Sağ panelde gösterilecek görev satırları (kritik üstte)."""
        try:
            return self._repo.ekip_gorevlerini_listele(self._ekip_id)
        except Exception as ex:
            raise RuntimeError(f"Görev listesi alınamadı: {ex}") from ex

    def gorev_olustur(
        self,
        baslik: str,
        aciklama: str,
        due_date_metni: str,
        kritiklik: str,
        atanan_kullanici_id: int,
        olusturan_kullanici_id: int,
    ) -> GorevOlusturSonuc:
        """
        Form doğrulaması + INSERT.

        due_date_metni boş ise NULL kaydedilir (opsiyonel teslim tarihi).
        Dolu ise YYYY-MM-DD formatında olmalıdır.
        """
        b = (baslik or "").strip()
        if not b:
            return GorevOlusturSonuc(False, "Görev başlığı boş bırakılamaz.")

        if kritiklik not in config.KRITIKLIK_SECENEKLERI:
            return GorevOlusturSonuc(False, "Geçersiz kritiklik seviyesi seçildi.")

        due: Optional[str] = None
        dm = (due_date_metni or "").strip()
        if dm:
            try:
                datetime.strptime(dm, "%Y-%m-%d")
            except ValueError:
                return GorevOlusturSonuc(
                    False,
                    "Son teslim tarihi YYYY-MM-DD formatında olmalıdır (örnek: 2026-05-10).",
                )
            due = dm

        if int(atanan_kullanici_id) <= 0:
            return GorevOlusturSonuc(False, "Lütfen atanacak yazılımcıyı seçin.")

        try:
            uygun = {int(x["kullanici_id"]) for x in self._repo.ekipteki_gelistirici_uyeler(self._ekip_id)}
        except Exception as ex:
            return GorevOlusturSonuc(False, f"Ekip üyeleri doğrulanamadı: {ex}")

        if int(atanan_kullanici_id) not in uygun:
            return GorevOlusturSonuc(False, "Seçilen kullanıcı bu ekipte atanabilir geliştirici değil.")

        try:
            yeni_id = self._repo.gorev_ekle(
                ekip_id=self._ekip_id,
                baslik=b,
                aciklama=(aciklama or "").strip(),
                kritiklik=kritiklik,
                olusturan_kullanici_id=int(olusturan_kullanici_id),
                atanan_kullanici_id=int(atanan_kullanici_id),
                due_date=due,
            )
        except Exception as ex:
            return GorevOlusturSonuc(False, f"Veritabanına kaydedilemedi: {ex}")

        self._audit.log_islem(
            "GOREV_OLUSTURULDU",
            f"Görev #{yeni_id} atandı.",
            kullanici_id=int(olusturan_kullanici_id),
            ekip_id=self._ekip_id,
            gorev_id=int(yeni_id),
        )
        acik = (aciklama or "").strip()
        self._features._repo.gorev_aktivite_ekle(
            int(yeni_id),
            "OLUSTURULDU",
            b,
            kullanici_id=int(olusturan_kullanici_id),
            ekip_id=self._ekip_id,
        )
        if acik:
            self._features.mention_isle(acik, self._ekip_id, int(yeni_id), int(olusturan_kullanici_id))
        return GorevOlusturSonuc(True, "Görev oluşturuldu ve yazılımcıya atandı.", yeni_gorev_id=int(yeni_id))

    def gorev_guncelle(
        self,
        gorev_id: int,
        baslik: str,
        aciklama: str,
        due_date_metni: str,
        kritiklik: str,
        yapan_kullanici_id: int = 0,
    ) -> tuple[bool, str]:
        b = (baslik or "").strip()
        if not b:
            return False, "Başlık boş olamaz."
        if kritiklik not in config.KRITIKLIK_SECENEKLERI:
            return False, "Geçersiz kritiklik."
        due: Optional[str] = None
        dm = (due_date_metni or "").strip()
        if dm:
            try:
                datetime.strptime(dm, "%Y-%m-%d")
                due = dm
            except ValueError:
                return False, "Tarih YYYY-MM-DD olmalı."
        try:
            self._repo.gorev_guncelle(
                int(gorev_id), self._ekip_id, b, (aciklama or "").strip(), kritiklik, due
            )
            self._audit.log_islem(
                "GOREV_GUNCELLENDI",
                f"Görev #{gorev_id} güncellendi.",
                ekip_id=self._ekip_id,
                gorev_id=int(gorev_id),
            )
            acik = (aciklama or "").strip()
            self._features._repo.gorev_aktivite_ekle(
                int(gorev_id),
                "GUNCELLENDI",
                b,
                ekip_id=self._ekip_id,
            )
            if acik and int(yapan_kullanici_id) > 0:
                self._features.mention_isle(
                    acik, self._ekip_id, int(gorev_id), int(yapan_kullanici_id)
                )
            return True, "Görev güncellendi."
        except Exception as ex:
            return False, str(ex)

    def gorev_sil(self, gorev_id: int) -> tuple[bool, str]:
        try:
            self._repo.gorev_sil(int(gorev_id), self._ekip_id)
            self._audit.log_islem(
                "GOREV_SILINDI",
                f"Görev #{gorev_id} silindi.",
                ekip_id=self._ekip_id,
                gorev_id=int(gorev_id),
            )
            return True, "Görev silindi."
        except Exception as ex:
            return False, str(ex)

    def denetim_loglari(self) -> list[dict[str, Any]]:
        return self._audit.ekip_loglarini_listele(self._ekip_id)

    def alt_gorevleri_getir(self, gorev_id: int) -> list[dict[str, Any]]:
        """Detay penceresi için alt görev listesi."""
        try:
            return self._repo.alt_gorevleri_listele(int(gorev_id))
        except Exception as ex:
            raise RuntimeError(f"Alt görevler okunamadı: {ex}") from ex

    def alt_gorev_ekle(self, gorev_id: int, baslik: str) -> tuple[bool, str]:
        """Yeni alt görev satırı ekler."""
        try:
            self._repo.alt_gorev_ekle(int(gorev_id), baslik)
            return True, ""
        except ValueError as ve:
            return False, str(ve)
        except Exception as ex:
            return False, f"Alt görev eklenemedi: {ex}"

    def alt_gorev_tamamlandi_kaydet(self, alt_gorev_id: int, tamamlandi: bool) -> tuple[bool, str]:
        """Checkbox değişimini kalıcı yazar."""
        try:
            self._repo.alt_gorev_tamamlandi_guncelle(int(alt_gorev_id), bool(tamamlandi))
            return True, ""
        except Exception as ex:
            return False, str(ex)
