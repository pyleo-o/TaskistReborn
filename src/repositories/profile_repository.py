# -*- coding: utf-8 -*-
"""profile_repository.py — Profil, arama, takip."""

from __future__ import annotations

from typing import Any, Optional

from src.db.connection import get_connection


class ProfileRepository:
    @staticmethod
    def kullanici_tam(kullanici_id: int) -> Optional[dict[str, Any]]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM Kullanicilar WHERE id = ? LIMIT 1", (int(kullanici_id),))
            row = cur.fetchone()
            return dict(row) if row else None

    @staticmethod
    def kullanici_ara(sorgu: str, limit: int = 20) -> list[dict[str, Any]]:
        q = (sorgu or "").strip().lstrip("@")
        if not q:
            return []
        like = f"%{q}%"
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, email, ad_soyad, kullanici_adi, profil_gizli, bio
                FROM Kullanicilar
                WHERE lower(email) LIKE lower(?)
                   OR lower(COALESCE(kullanici_adi, '')) LIKE lower(?)
                   OR lower(ad_soyad) LIKE lower(?)
                LIMIT ?
                """,
                (like, like, like, int(limit)),
            )
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def profil_guncelle(
        kullanici_id: int,
        ad_soyad: str,
        bio: str,
        kullanici_adi: str,
        profil_gizli: bool,
        tercih_tema: Optional[str] = None,
    ) -> None:
        with get_connection() as conn:
            cur = conn.cursor()
            if tercih_tema:
                cur.execute(
                    """
                    UPDATE Kullanicilar
                    SET ad_soyad = ?, bio = ?, kullanici_adi = ?, profil_gizli = ?, tercih_tema = ?
                    WHERE id = ?
                    """,
                    (ad_soyad, bio, kullanici_adi, 1 if profil_gizli else 0, tercih_tema, int(kullanici_id)),
                )
            else:
                cur.execute(
                    """
                    UPDATE Kullanicilar
                    SET ad_soyad = ?, bio = ?, kullanici_adi = ?, profil_gizli = ?
                    WHERE id = ?
                    """,
                    (ad_soyad, bio, kullanici_adi, 1 if profil_gizli else 0, int(kullanici_id)),
                )
            conn.commit()

    @staticmethod
    def sifre_guncelle(kullanici_id: int, yeni_hash: str) -> None:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE Kullanicilar SET sifre = ? WHERE id = ?", (yeni_hash, int(kullanici_id)))
            conn.commit()

    @staticmethod
    def takip_et(takip_eden_id: int, takip_edilen_id: int) -> None:
        if int(takip_eden_id) == int(takip_edilen_id):
            raise ValueError("Kendinizi takip edemezsiniz.")
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO Takipler (takip_eden_id, takip_edilen_id) VALUES (?, ?)",
                (int(takip_eden_id), int(takip_edilen_id)),
            )
            conn.commit()

    @staticmethod
    def takibi_birak(takip_eden_id: int, takip_edilen_id: int) -> None:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM Takipler WHERE takip_eden_id = ? AND takip_edilen_id = ?",
                (int(takip_eden_id), int(takip_edilen_id)),
            )
            conn.commit()

    @staticmethod
    def takip_ediyor_mu(takip_eden_id: int, takip_edilen_id: int) -> bool:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT 1 FROM Takipler WHERE takip_eden_id = ? AND takip_edilen_id = ? LIMIT 1",
                (int(takip_eden_id), int(takip_edilen_id)),
            )
            return cur.fetchone() is not None

    @staticmethod
    def takip_sayilari(kullanici_id: int) -> dict[str, int]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS c FROM Takipler WHERE takip_eden_id = ?", (int(kullanici_id),))
            edilen = int(cur.fetchone()["c"])
            cur.execute("SELECT COUNT(*) AS c FROM Takipler WHERE takip_edilen_id = ?", (int(kullanici_id),))
            eden = int(cur.fetchone()["c"])
            return {"takip_edilen": edilen, "takipci": eden}

    @staticmethod
    def kullanici_ekipleri(kullanici_id: int) -> list[dict[str, Any]]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT e.id AS ekip_id, e.ad AS ekip_ad, r.rol_adi, e.olusturan_kullanici_id
                FROM Ekip_Uyeleri eu
                JOIN Ekipler e ON e.id = eu.ekip_id
                JOIN Roller r ON r.id = eu.rol_id
                WHERE eu.kullanici_id = ?
                ORDER BY e.ad COLLATE NOCASE
                """,
                (int(kullanici_id),),
            )
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def olusturdugu_ekipler(kullanici_id: int) -> list[dict[str, Any]]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, ad, aciklama, olusturma_tarihi FROM Ekipler WHERE olusturan_kullanici_id = ?",
                (int(kullanici_id),),
            )
            return [dict(r) for r in cur.fetchall()]
