# -*- coding: utf-8 -*-
"""users_repository.py — Kullanicilar tablosu."""

from __future__ import annotations

from typing import Any, Optional

from src.db.connection import get_connection


class UsersRepository:
    @staticmethod
    def kullanici_giris_ile_bul(kimlik: str) -> Optional[dict[str, Any]]:
        """E-posta veya @kullanici_adi ile kullanıcı bulur."""
        q = (kimlik or "").strip()
        if not q:
            return None
        if "@" in q:
            return UsersRepository.kullanici_email_ile_bul(q)
        return UsersRepository.kullanici_kadi_ile_bul(q.lstrip("@"))

    @staticmethod
    def kullanici_kadi_ile_bul(kullanici_adi: str) -> Optional[dict[str, Any]]:
        kadi = (kullanici_adi or "").strip().lower()
        if not kadi:
            return None
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, email, sifre, ad_soyad, olusturma_tarihi,
                       kullanici_adi, bio, profil_gizli, tercih_tema, avatar_yolu
                FROM Kullanicilar
                WHERE lower(trim(kullanici_adi)) = ?
                LIMIT 1
                """,
                (kadi,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    @staticmethod
    def kullanici_email_ile_bul(email: str) -> Optional[dict[str, Any]]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, email, sifre, ad_soyad, olusturma_tarihi,
                       kullanici_adi, bio, profil_gizli, tercih_tema, avatar_yolu
                FROM Kullanicilar
                WHERE lower(trim(email)) = lower(trim(?))
                LIMIT 1
                """,
                (email,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    @staticmethod
    def kullanici_id_ile_bul(kullanici_id: int) -> Optional[dict[str, Any]]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, email, ad_soyad, olusturma_tarihi, kullanici_adi, bio, profil_gizli, avatar_yolu
                FROM Kullanicilar WHERE id = ? LIMIT 1
                """,
                (int(kullanici_id),),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    @staticmethod
    def kullanici_ekle(
        email: str,
        sifre: str,
        ad_soyad: str,
        kullanici_adi: Optional[str] = None,
        avatar_yolu: Optional[str] = None,
    ) -> int:
        kadi = (kullanici_adi or "").strip().lower() or email.split("@", 1)[0].lower()
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO Kullanicilar (email, sifre, ad_soyad, kullanici_adi, avatar_yolu)
                VALUES (lower(trim(?)), ?, ?, ?, ?)
                """,
                (email, sifre, ad_soyad.strip(), kadi, avatar_yolu),
            )
            conn.commit()
            return int(cur.lastrowid)

    @staticmethod
    def avatar_guncelle(kullanici_id: int, avatar_yolu: Optional[str]) -> None:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE Kullanicilar SET avatar_yolu = ? WHERE id = ?",
                (avatar_yolu, int(kullanici_id)),
            )
            conn.commit()

    @staticmethod
    def sifre_guncelle(kullanici_id: int, yeni_sifre: str) -> None:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE Kullanicilar SET sifre = ? WHERE id = ?", (yeni_sifre, int(kullanici_id)))
            conn.commit()
