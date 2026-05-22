# -*- coding: utf-8 -*-
"""profile_service.py — Profil ve portföy iş kuralları."""

from __future__ import annotations

import re
from typing import Any, Optional

from src.repositories.profile_repository import ProfileRepository
from src.repositories.tasks_repository import TasksRepository
from src.repositories.users_repository import UsersRepository
from src.services.avatar_service import AvatarService
from src.utils.password_util import sifre_dogrula, sifre_hashle


class ProfileService:
    def __init__(
        self,
        profile_repo: Optional[ProfileRepository] = None,
        tasks_repo: Optional[TasksRepository] = None,
        avatar_svc: Optional[AvatarService] = None,
    ) -> None:
        self._profil = profile_repo or ProfileRepository()
        self._tasks = tasks_repo or TasksRepository()
        self._avatars = avatar_svc or AvatarService()
        self._users = UsersRepository()

    def profil_getir(self, hedef_id: int, izleyen_id: Optional[int] = None) -> Optional[dict[str, Any]]:
        row = self._profil.kullanici_tam(int(hedef_id))
        if row is None:
            return None
        gizli = bool(int(row.get("profil_gizli") or 0))
        benim = izleyen_id is not None and int(izleyen_id) == int(hedef_id)
        if gizli and not benim:
            return {
                "id": row["id"],
                "kullanici_adi": row.get("kullanici_adi") or row["email"].split("@")[0],
                "profil_gizli": True,
                "gosterim": "Bu profil gizli.",
            }
        istat = self._tasks.kullanici_gorev_istatistik(int(hedef_id))
        takip = self._profil.takip_sayilari(int(hedef_id))
        return {
            **row,
            "profil_gizli": False,
            "ekipler": self._profil.kullanici_ekipleri(int(hedef_id)),
            "olusturdugu_ekipler": self._profil.olusturdugu_ekipler(int(hedef_id)),
            "gorev_istatistik": istat,
            "takip_sayilari": takip,
            "takip_ediyorum": (
                self._profil.takip_ediyor_mu(int(izleyen_id), int(hedef_id))
                if izleyen_id and not benim
                else False
            ),
        }

    def ara(self, sorgu: str) -> list[dict[str, Any]]:
        return self._profil.kullanici_ara(sorgu)

    def profil_kaydet(
        self,
        kullanici_id: int,
        ad_soyad: str,
        bio: str,
        kullanici_adi: str,
        profil_gizli: bool,
        tercih_tema: Optional[str] = None,
    ) -> tuple[bool, str]:
        kadi = (kullanici_adi or "").strip().lower()
        if not kadi:
            return False, "Kullanıcı adı zorunludur."
        if not re.match(r"^[a-z0-9_]{3,30}$", kadi):
            return False, "Kullanıcı adı 3-30 karakter, harf/rakam/alt çizgi olmalı."
        try:
            self._profil.profil_guncelle(
                int(kullanici_id), ad_soyad.strip(), bio.strip(), kadi, profil_gizli, tercih_tema
            )
        except Exception as ex:
            return False, f"Kayıt hatası: {ex}"
        return True, "Profil güncellendi."

    def sifre_degistir(self, kullanici_id: int, eski: str, yeni: str) -> tuple[bool, str]:
        row = self._profil.kullanici_tam(int(kullanici_id))
        if row is None:
            return False, "Kullanıcı bulunamadı."
        kayitli = str(row.get("sifre") or "")
        if not sifre_dogrula(eski, kayitli):
            return False, "Mevcut şifre hatalı."
        if len(yeni) < 4:
            return False, "Yeni şifre en az 4 karakter olmalı."
        self._profil.sifre_guncelle(int(kullanici_id), sifre_hashle(yeni))
        return True, "Şifre güncellendi."

    def takip_et(self, eden: int, edilen: int) -> tuple[bool, str]:
        try:
            self._profil.takip_et(int(eden), int(edilen))
        except ValueError as ve:
            return False, str(ve)
        return True, "Takip ediliyor."

    def takibi_birak(self, eden: int, edilen: int) -> None:
        self._profil.takibi_birak(int(eden), int(edilen))

    def avatar_yukle(self, kullanici_id: int, dosya_yolu: str) -> tuple[bool, str]:
        try:
            yol = self._avatars.yukle(int(kullanici_id), dosya_yolu)
            self._users.avatar_guncelle(int(kullanici_id), yol)
            return True, "Profil fotoğrafı güncellendi."
        except Exception as ex:
            return False, str(ex)

    def avatar_sil(self, kullanici_id: int) -> tuple[bool, str]:
        try:
            yol = self._avatars.sil(int(kullanici_id))
            self._users.avatar_guncelle(int(kullanici_id), yol)
            return True, "Varsayılan avatar atandı."
        except Exception as ex:
            return False, str(ex)
