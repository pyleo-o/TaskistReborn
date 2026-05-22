# -*- coding: utf-8 -*-
"""
workspace_service.py — Ekip (workspace) seçimi ve oluşturma iş kuralları.

Kullanıcının rolü global değildir; her ekip için Ekip_Uyeleri satırından çözülür.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any, Optional

from src.repositories.teams_repository import TeamsRepository
from src.repositories.users_repository import UsersRepository


@dataclass
class EkipOlusturmaSonucu:
    basarili: bool
    ekip_id: Optional[int]
    mesaj: str


@dataclass
class DavetSonucu:
    """Ekip üyesi davet işlemi sonucu."""

    basarili: bool
    mesaj: str


class WorkspaceService:
    """Ekip listeleme / oluşturma ve üyelik doğrulama."""

    def __init__(
        self,
        teams_repo: Optional[TeamsRepository] = None,
        users_repo: Optional[UsersRepository] = None,
    ) -> None:
        self._teams = teams_repo or TeamsRepository()
        self._users = users_repo or UsersRepository()

    def ekiplerimi_listele(self, kullanici_id: int) -> list[dict[str, Any]]:
        """
        Oturum açmış kullanıcının görebileceği ekip kartları için veri döndürür.

        Her satır: ekip_id, ekip_ad, ekip_aciklama, rol_adi, rol_id, katilim_tarihi
        """
        try:
            return self._teams.kullanicinin_ekipleri(int(kullanici_id))
        except Exception as ex:
            raise RuntimeError(f"Ekip listesi okunamadı: {ex}") from ex

    def ekipte_rolu_al(self, kullanici_id: int, ekip_id: int) -> Optional[dict[str, Any]]:
        """
        Seçilen ekipte kullanıcının rolünü döndürür.

        Dönüş örneği: {"ekip_id": 1, "ekip_ad": "...", "rol_id": 2, "rol_adi": "Tester"}
        Üyelik yoksa None (UI bu durumda uyarı göstermelidir).
        """
        try:
            return self._teams.uyelik_getir(int(kullanici_id), int(ekip_id))
        except Exception as ex:
            raise RuntimeError(f"Üyelik sorgusu başarısız: {ex}") from ex

    def yeni_ekip_olustur(self, kullanici_id: int, ad: str, aciklama: str) -> EkipOlusturmaSonucu:
        """
        Yeni çalışma alanı açar; oluşturan kullanıcı otomatik 'Yönetici' üyesi olur.

        Davet / kullanıcı arama modülü bilinçli olarak bu aşamada yoktur.
        """
        if not (ad or "").strip():
            return EkipOlusturmaSonucu(False, None, "Ekip adı boş olamaz.")

        try:
            yeni_id = self._teams.ekip_olustur_ve_yoneticiyi_ekle(
                ad=ad,
                aciklama=aciklama,
                olusturan_kullanici_id=int(kullanici_id),
            )
            return EkipOlusturmaSonucu(True, int(yeni_id), "")
        except ValueError as ve:
            return EkipOlusturmaSonucu(False, None, str(ve))
        except Exception as ex:
            return EkipOlusturmaSonucu(
                False,
                None,
                f"Ekip oluşturulamadı: {ex}\nVeritabanı izinlerini veya kilit durumunu kontrol edin.",
            )

    def tum_rol_secenekleri(self) -> list[str]:
        """Davet formu için Roller tablosundaki adlar."""
        try:
            return self._teams.tum_rolleri_adi_listesi()
        except Exception as ex:
            raise RuntimeError(f"Rol listesi alınamadı: {ex}") from ex

    def uyeyi_davet_et(
        self,
        ekip_id: int,
        davet_eden_kullanici_id: int,
        hedef_email: str,
        rol_adi: str,
    ) -> DavetSonucu:
        """
        Kayıtlı bir kullanıcıyı e-posta ile bulur ve seçilen rolle ekibe ekler.

        Kurallar:
        - Davet eden kullanıcı ilgili ekipte 'Yönetici' olmalıdır.
        - Hedef kullanıcı sistemde kayıtlı olmalıdır (Kayıt Olmuş).
        - Aynı ekipte zaten üye ise ekleme yapılmaz.
        """
        if not self._teams.ekipte_yonetici_mi(int(ekip_id), int(davet_eden_kullanici_id)):
            return DavetSonucu(False, "Bu işlem için ekipte 'Yönetici' rolüne sahip olmalısınız.")

        em = (hedef_email or "").strip()
        if not em or "@" not in em:
            return DavetSonucu(False, "Geçerli bir hedef e-posta giriniz.")

        try:
            hedef = self._users.kullanici_email_ile_bul(em)
        except Exception as ex:
            return DavetSonucu(False, f"Kullanıcı sorgulanamadı: {ex}")

        if hedef is None:
            return DavetSonucu(
                False,
                "Bu e-posta ile kayıtlı kullanıcı bulunamadı. Önce 'Kayıt Ol' ile hesap oluşturmalıdır.",
            )

        hid = int(hedef["id"])
        if hid == int(davet_eden_kullanici_id):
            return DavetSonucu(False, "Kendinizi davet edemezsiniz.")

        if self._teams.uyelik_getir(hid, int(ekip_id)) is not None:
            return DavetSonucu(False, "Bu kullanıcı zaten bu ekibe üye.")

        rid = self._teams.rol_id_rol_adindan((rol_adi or "").strip())
        if rid is None:
            return DavetSonucu(False, "Geçersiz rol seçimi.")

        try:
            self._teams.ekip_uye_ekle(int(ekip_id), hid, int(rid))
        except sqlite3.IntegrityError:
            return DavetSonucu(False, "Üyelik eklenemedi: kullanıcı zaten bu ekibe kayıtlı olabilir.")
        except Exception as ex:
            return DavetSonucu(False, f"Üyelik eklenemedi: {ex}")

        return DavetSonucu(True, "Kullanıcı ekibe eklendi.")
