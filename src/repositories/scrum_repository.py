# -*- coding: utf-8 -*-
"""scrum_repository.py — ScrumGunluk tablosu."""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from src.db.connection import get_connection


class ScrumRepository:
    @staticmethod
    def bugun_kayit_var_mi(kullanici_id: int, ekip_id: int, tarih: Optional[str] = None) -> bool:
        t = tarih or date.today().isoformat()
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 1 FROM ScrumGunluk
                WHERE kullanici_id = ? AND ekip_id = ? AND tarih = ?
                LIMIT 1
                """,
                (int(kullanici_id), int(ekip_id), t),
            )
            return cur.fetchone() is not None

    @staticmethod
    def kaydet(
        kullanici_id: int,
        ekip_id: int,
        dun: str,
        bugun: str,
        engel: str,
        tarih: Optional[str] = None,
    ) -> None:
        t = tarih or date.today().isoformat()
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO ScrumGunluk (kullanici_id, ekip_id, tarih, dun_yaptiklarim, bugun_yapacaklarim, engel_var_mi)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(kullanici_id, ekip_id, tarih) DO UPDATE SET
                    dun_yaptiklarim = excluded.dun_yaptiklarim,
                    bugun_yapacaklarim = excluded.bugun_yapacaklarim,
                    engel_var_mi = excluded.engel_var_mi
                """,
                (int(kullanici_id), int(ekip_id), t, dun, bugun, engel),
            )
            conn.commit()

    @staticmethod
    def ekip_gunluk_ozet(ekip_id: int, tarih: Optional[str] = None) -> list[dict[str, Any]]:
        t = tarih or date.today().isoformat()
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT s.*, COALESCE(NULLIF(TRIM(k.ad_soyad), ''), k.email) AS kullanici_gosterim
                FROM ScrumGunluk s
                JOIN Kullanicilar k ON k.id = s.kullanici_id
                WHERE s.ekip_id = ? AND s.tarih = ?
                ORDER BY kullanici_gosterim COLLATE NOCASE
                """,
                (int(ekip_id), t),
            )
            return [dict(r) for r in cur.fetchall()]
