# -*- coding: utf-8 -*-
"""notifications_repository.py — Bildirimler tablosu."""

from __future__ import annotations

from typing import Any, Optional

from src.db.connection import get_connection


class NotificationsRepository:
    @staticmethod
    def ekle(
        kullanici_id: int,
        baslik: str,
        mesaj: str,
        tip: str = "GENEL",
        ekip_id: Optional[int] = None,
        ilgili_kullanici_id: Optional[int] = None,
        ilgili_kayit_id: Optional[int] = None,
    ) -> int:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO Bildirimler (
                    kullanici_id, ekip_id, baslik, mesaj, tip,
                    ilgili_kullanici_id, ilgili_kayit_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(kullanici_id),
                    ekip_id,
                    baslik,
                    mesaj,
                    tip,
                    ilgili_kullanici_id,
                    ilgili_kayit_id,
                ),
            )
            conn.commit()
            return int(cur.lastrowid)

    @staticmethod
    def kullanici_bildirimleri(kullanici_id: int, limit: int = 50) -> list[dict[str, Any]]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, baslik, mesaj, okundu, tip, ekip_id, olusturma_tarihi,
                       ilgili_kullanici_id, ilgili_kayit_id
                FROM Bildirimler
                WHERE kullanici_id = ?
                ORDER BY olusturma_tarihi DESC
                LIMIT ?
                """,
                (int(kullanici_id), int(limit)),
            )
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def okunmamis_sayisi(kullanici_id: int) -> int:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) AS c FROM Bildirimler WHERE kullanici_id = ? AND okundu = 0",
                (int(kullanici_id),),
            )
            return int(cur.fetchone()["c"])

    @staticmethod
    def okundu_isaretle(bildirim_id: int, kullanici_id: int) -> None:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE Bildirimler SET okundu = 1 WHERE id = ? AND kullanici_id = ?",
                (int(bildirim_id), int(kullanici_id)),
            )
            conn.commit()

    @staticmethod
    def tumunu_okundu(kullanici_id: int) -> None:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE Bildirimler SET okundu = 1 WHERE kullanici_id = ?",
                (int(kullanici_id),),
            )
            conn.commit()
