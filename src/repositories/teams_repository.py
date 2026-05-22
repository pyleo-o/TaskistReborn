# -*- coding: utf-8 -*-
"""
teams_repository.py — Ekipler, Ekip_Uyeleri ve rol çözümü sorguları.

Many-to-many köprü tablosu: Ekip_Uyeleri (ekip_id, kullanici_id, rol_id).
"""

from __future__ import annotations

from typing import Any, Optional

import src.config as config
from src.db.connection import get_connection


class TeamsRepository:
    """Workspace (ekip) ve üyelik sorguları."""

    @staticmethod
    def rol_id_rol_adindan(rol_adi: str) -> Optional[int]:
        """Roller tablosundan rol adına göre id döndürür."""
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM Roller WHERE rol_adi = ? LIMIT 1", (rol_adi,))
            row = cur.fetchone()
            return int(row["id"]) if row else None

    @staticmethod
    def kullanicinin_ekipleri(kullanici_id: int) -> list[dict[str, Any]]:
        """
        Kullanıcının üye olduğu tüm ekipleri, o ekipteki rolü ile listeler.

        Dönüş alanları: ekip_id, ekip_ad, ekip_aciklama, rol_id, rol_adi, katilim_tarihi
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    e.id AS ekip_id,
                    e.ad AS ekip_ad,
                    e.aciklama AS ekip_aciklama,
                    eu.rol_id AS rol_id,
                    r.rol_adi AS rol_adi,
                    eu.katilim_tarihi AS katilim_tarihi
                FROM Ekip_Uyeleri eu
                JOIN Ekipler e ON e.id = eu.ekip_id
                JOIN Roller r ON r.id = eu.rol_id
                WHERE eu.kullanici_id = ?
                ORDER BY e.ad COLLATE NOCASE
                """,
                (int(kullanici_id),),
            )
            return [dict(row) for row in cur.fetchall()]

    @staticmethod
    def uyelik_getir(kullanici_id: int, ekip_id: int) -> Optional[dict[str, Any]]:
        """
        Belirli ekipte kullanıcının üyeliğini döndürür (yoksa None).

        Dönüş: ekip_id, rol_id, rol_adi, ekip_ad
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    e.id AS ekip_id,
                    e.ad AS ekip_ad,
                    eu.rol_id AS rol_id,
                    r.rol_adi AS rol_adi
                FROM Ekip_Uyeleri eu
                JOIN Ekipler e ON e.id = eu.ekip_id
                JOIN Roller r ON r.id = eu.rol_id
                WHERE eu.kullanici_id = ? AND eu.ekip_id = ?
                LIMIT 1
                """,
                (int(kullanici_id), int(ekip_id)),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    @staticmethod
    def ekip_olustur_ve_yoneticiyi_ekle(
        ad: str,
        aciklama: str,
        olusturan_kullanici_id: int,
    ) -> int:
        """
        Yeni ekip kaydı oluşturur ve oluşturan kullanıcıyı otomatik 'Yönetici' rolü ile üye yapar.

        İşlem atomik olmalı: hata olursa exception fırlatılır, commit yapılmaz.

        Returns:
            Yeni ekip_id.
        """
        ad_trim = ad.strip()
        if not ad_trim:
            raise ValueError("Ekip adı boş olamaz.")

        yonetici_rol_id = TeamsRepository.rol_id_rol_adindan(config.ROL_YONETICI)
        if yonetici_rol_id is None:
            raise RuntimeError("Roller tablosunda 'Yönetici' rolü bulunamadı. init_database çalıştırın.")

        with get_connection() as conn:
            try:
                conn.execute("PRAGMA foreign_keys = ON")
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO Ekipler (ad, aciklama, olusturan_kullanici_id)
                    VALUES (?, ?, ?)
                    """,
                    (ad_trim, (aciklama or "").strip(), int(olusturan_kullanici_id)),
                )
                ekip_id = int(cur.lastrowid)
                cur.execute(
                    """
                    INSERT INTO Ekip_Uyeleri (ekip_id, kullanici_id, rol_id)
                    VALUES (?, ?, ?)
                    """,
                    (ekip_id, int(olusturan_kullanici_id), int(yonetici_rol_id)),
                )
                conn.commit()
                return ekip_id
            except Exception:
                conn.rollback()
                raise

    @staticmethod
    def tum_rolleri_adi_listesi() -> list[str]:
        """Davet formunda kullanılacak rol adları (Roller tablosundan)."""
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT rol_adi FROM Roller ORDER BY id ASC")
            return [str(r["rol_adi"]) for r in cur.fetchall()]

    @staticmethod
    def ekipte_yonetici_mi(ekip_id: int, kullanici_id: int) -> bool:
        """Kullanıcı bu ekipte 'Yönetici' rolünde mi? (davet yetkisi için)."""
        uy = TeamsRepository.uyelik_getir(int(kullanici_id), int(ekip_id))
        if uy is None:
            return False
        return str(uy.get("rol_adi")) == config.ROL_YONETICI

    @staticmethod
    def ekip_uye_ekle(ekip_id: int, hedef_kullanici_id: int, rol_id: int) -> None:
        """
        Ekip_Uyeleri tablosuna satır ekler.

        UNIQUE(ekip_id, kullanici_id) ihlalinde sqlite3.IntegrityError fırlar.
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO Ekip_Uyeleri (ekip_id, kullanici_id, rol_id)
                VALUES (?, ?, ?)
                """,
                (int(ekip_id), int(hedef_kullanici_id), int(rol_id)),
            )
            conn.commit()
