# -*- coding: utf-8 -*-
"""auth_service.py — Kimlik doğrulama."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any, Optional

from src.repositories.users_repository import UsersRepository
from src.services.avatar_service import AvatarService
from src.utils.password_util import hash_mi, sifre_dogrula, sifre_hashle


@dataclass
class GirisSonucu:
    basarili: bool
    kullanici: Optional[dict[str, Any]]
    mesaj: str


class AuthService:
    def __init__(
        self,
        users_repo: Optional[UsersRepository] = None,
        avatar_svc: Optional[AvatarService] = None,
    ) -> None:
        self._users = users_repo or UsersRepository()
        self._avatars = avatar_svc or AvatarService()

    def giris_yap(self, kimlik: str, sifre: str) -> GirisSonucu:
        """kimlik: e-posta veya kullanıcı adı (@ isteğe bağlı)."""
        em = (kimlik or "").strip()
        sf = sifre or ""

        if not em:
            return GirisSonucu(False, None, "E-posta veya kullanıcı adı giriniz.")
        if not sf.strip():
            return GirisSonucu(False, None, "Şifre alanı boş bırakılamaz.")

        try:
            row = self._users.kullanici_giris_ile_bul(em)
        except Exception as ex:
            return GirisSonucu(False, None, f"Veritabanı hatası: {ex}")

        if row is None:
            return GirisSonucu(False, None, "Kullanıcı bulunamadı. E-posta veya kullanıcı adını kontrol edin.")

        kayitli = str(row.get("sifre") or "")
        if not sifre_dogrula(sf, kayitli):
            return GirisSonucu(False, None, "Şifre hatalı.")

        if not hash_mi(kayitli):
            try:
                self._users.sifre_guncelle(int(row["id"]), sifre_hashle(sf))
            except Exception:
                pass

        kullanici_ozet = {
            "id": int(row["id"]),
            "email": row["email"],
            "ad_soyad": row.get("ad_soyad") or "",
            "kullanici_adi": row.get("kullanici_adi") or "",
            "avatar_yolu": row.get("avatar_yolu"),
        }
        return GirisSonucu(True, kullanici_ozet, "")

    def kayit_ol(
        self,
        email: str,
        sifre: str,
        ad_soyad: str,
        kullanici_adi: str = "",
    ) -> GirisSonucu:
        em = (email or "").strip()
        sf = sifre or ""
        ad = (ad_soyad or "").strip()
        kadi = (kullanici_adi or "").strip().lower()

        if not em or "@" not in em:
            return GirisSonucu(False, None, "Geçerli e-posta giriniz.")
        if len(sf) < 4:
            return GirisSonucu(False, None, "Şifre en az 4 karakter olmalıdır.")

        try:
            uid = self._users.kullanici_ekle(
                em, sifre_hashle(sf), ad or em.split("@", 1)[0], kadi or None, avatar_yolu=None
            )
            av = self._avatars.kayittan_ata(int(uid))
            self._users.avatar_guncelle(int(uid), av)
        except sqlite3.IntegrityError:
            return GirisSonucu(False, None, "E-posta veya kullanıcı adı zaten kayıtlı.")
        except Exception as ex:
            return GirisSonucu(False, None, f"Kayıt hatası: {ex}")

        return GirisSonucu(True, None, "Kayıt başarılı. Giriş yapabilirsiniz.")
