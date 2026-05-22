# -*- coding: utf-8 -*-
"""social_repository.py — Davet, katılım isteği, gönderi ve beğeni."""

from __future__ import annotations

from typing import Any, Optional

import src.config as config
from src.db.connection import get_connection


class SocialRepository:
    # --- Davetler ---
    @staticmethod
    def davet_ekle(ekip_id: int, hedef_id: int, davet_eden_id: int, rol_id: int) -> int:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO Ekip_Davetleri (ekip_id, hedef_kullanici_id, davet_eden_id, rol_id, durum)
                VALUES (?, ?, ?, ?, ?)
                """,
                (int(ekip_id), int(hedef_id), int(davet_eden_id), int(rol_id), config.DAVET_DURUM_BEKLEMEDE),
            )
            conn.commit()
            return int(cur.lastrowid)

    @staticmethod
    def davet_bekleyen_var_mi(ekip_id: int, hedef_id: int) -> bool:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 1 FROM Ekip_Davetleri
                WHERE ekip_id = ? AND hedef_kullanici_id = ? AND durum = ?
                LIMIT 1
                """,
                (int(ekip_id), int(hedef_id), config.DAVET_DURUM_BEKLEMEDE),
            )
            return cur.fetchone() is not None

    @staticmethod
    def davet_getir(davet_id: int) -> Optional[dict[str, Any]]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT d.*, e.ad AS ekip_ad, r.rol_adi
                FROM Ekip_Davetleri d
                JOIN Ekipler e ON e.id = d.ekip_id
                JOIN Roller r ON r.id = d.rol_id
                WHERE d.id = ?
                """,
                (int(davet_id),),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    @staticmethod
    def davet_durum_guncelle(davet_id: int, durum: str) -> None:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE Ekip_Davetleri SET durum = ? WHERE id = ?", (durum, int(davet_id)))
            conn.commit()

    @staticmethod
    def bekleyen_davetler(kullanici_id: int) -> list[dict[str, Any]]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT d.id, d.ekip_id, d.rol_id, d.olusturma_tarihi,
                       e.ad AS ekip_ad, r.rol_adi,
                       u.ad_soyad AS davet_eden_ad, u.kullanici_adi AS davet_eden_kadi,
                       u.id AS davet_eden_id
                FROM Ekip_Davetleri d
                JOIN Ekipler e ON e.id = d.ekip_id
                JOIN Roller r ON r.id = d.rol_id
                JOIN Kullanicilar u ON u.id = d.davet_eden_id
                WHERE d.hedef_kullanici_id = ? AND d.durum = ?
                ORDER BY d.olusturma_tarihi DESC
                """,
                (int(kullanici_id), config.DAVET_DURUM_BEKLEMEDE),
            )
            return [dict(r) for r in cur.fetchall()]

    # --- Katılım istekleri ---
    @staticmethod
    def katilim_istegi_ekle(ekip_id: int, kullanici_id: int, mesaj: str = "") -> int:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO Ekip_Katilim_Istekleri (ekip_id, kullanici_id, durum, mesaj)
                VALUES (?, ?, ?, ?)
                """,
                (int(ekip_id), int(kullanici_id), config.KATILIM_DURUM_BEKLEMEDE, (mesaj or "").strip()),
            )
            conn.commit()
            return int(cur.lastrowid)

    @staticmethod
    def katilim_bekleyen_var_mi(ekip_id: int, kullanici_id: int) -> bool:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 1 FROM Ekip_Katilim_Istekleri
                WHERE ekip_id = ? AND kullanici_id = ? AND durum = ?
                LIMIT 1
                """,
                (int(ekip_id), int(kullanici_id), config.KATILIM_DURUM_BEKLEMEDE),
            )
            return cur.fetchone() is not None

    @staticmethod
    def katilim_istegi_getir(istek_id: int) -> Optional[dict[str, Any]]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ki.*, e.ad AS ekip_ad, e.olusturan_kullanici_id,
                       u.ad_soyad, u.kullanici_adi, u.email
                FROM Ekip_Katilim_Istekleri ki
                JOIN Ekipler e ON e.id = ki.ekip_id
                JOIN Kullanicilar u ON u.id = ki.kullanici_id
                WHERE ki.id = ?
                """,
                (int(istek_id),),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    @staticmethod
    def katilim_durum_guncelle(istek_id: int, durum: str) -> None:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE Ekip_Katilim_Istekleri SET durum = ? WHERE id = ?",
                (durum, int(istek_id)),
            )
            conn.commit()

    @staticmethod
    def ekip_bekleyen_katilim_istekleri(ekip_id: int) -> list[dict[str, Any]]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ki.id, ki.kullanici_id, ki.mesaj, ki.olusturma_tarihi,
                       u.ad_soyad, u.kullanici_adi, u.email, u.avatar_yolu
                FROM Ekip_Katilim_Istekleri ki
                JOIN Kullanicilar u ON u.id = ki.kullanici_id
                WHERE ki.ekip_id = ? AND ki.durum = ?
                ORDER BY ki.olusturma_tarihi DESC
                """,
                (int(ekip_id), config.KATILIM_DURUM_BEKLEMEDE),
            )
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def ekip_olusturan_id(ekip_id: int) -> Optional[int]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT olusturan_kullanici_id FROM Ekipler WHERE id = ?", (int(ekip_id),))
            row = cur.fetchone()
            return int(row["olusturan_kullanici_id"]) if row else None

    @staticmethod
    def kesfedilebilir_ekipler(kullanici_id: int, limit: int = 20) -> list[dict[str, Any]]:
        """Üye olunmayan, herkese açık ekipler."""
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT e.id AS ekip_id, e.ad AS ekip_ad, e.aciklama AS ekip_aciklama,
                       u.ad_soyad AS olusturan_ad, u.kullanici_adi AS olusturan_kadi,
                       (SELECT COUNT(*) FROM Ekip_Uyeleri eu WHERE eu.ekip_id = e.id) AS uye_sayisi
                FROM Ekipler e
                JOIN Kullanicilar u ON u.id = e.olusturan_kullanici_id
                WHERE COALESCE(e.herkese_acik, 1) = 1
                  AND e.id NOT IN (
                      SELECT ekip_id FROM Ekip_Uyeleri WHERE kullanici_id = ?
                  )
                ORDER BY e.olusturma_tarihi DESC
                LIMIT ?
                """,
                (int(kullanici_id), int(limit)),
            )
            return [dict(r) for r in cur.fetchall()]

    # --- Gönderiler ---
    @staticmethod
    def gonderi_ekle(
        kullanici_id: int,
        icerik: str,
        ekip_id: Optional[int] = None,
        gorunurluk: str = config.GORUNURLUK_HERKES,
    ) -> int:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO Gonderiler (kullanici_id, ekip_id, icerik, gorunurluk) VALUES (?, ?, ?, ?)",
                (int(kullanici_id), ekip_id, (icerik or "").strip(), gorunurluk),
            )
            conn.commit()
            return int(cur.lastrowid)

    @staticmethod
    def kullanici_gonderileri(
        kullanici_id: int,
        izleyen_id: Optional[int] = None,
        limit: int = 30,
    ) -> list[dict[str, Any]]:
        """Bir kullanıcının paylaştığı gönderiler (profil sayfası)."""
        izleyen = int(izleyen_id) if izleyen_id is not None else int(kullanici_id)
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT g.id, g.icerik, g.olusturma_tarihi, g.ekip_id,
                       COALESCE(g.gorunurluk, 'herkes') AS gorunurluk,
                       u.id AS yazar_id, u.ad_soyad, u.kullanici_adi, u.avatar_yolu,
                       e.ad AS ekip_ad,
                       (SELECT COUNT(*) FROM Gonderi_Begeniler b WHERE b.gonderi_id = g.id) AS begeni_sayisi,
                       EXISTS(
                           SELECT 1 FROM Gonderi_Begeniler b2
                           WHERE b2.gonderi_id = g.id AND b2.kullanici_id = ?
                       ) AS begendim,
                       EXISTS(
                           SELECT 1 FROM Gonderi_Kayitlari k
                           WHERE k.gonderi_id = g.id AND k.kullanici_id = ?
                       ) AS kayitli
                FROM Gonderiler g
                JOIN Kullanicilar u ON u.id = g.kullanici_id
                LEFT JOIN Ekipler e ON e.id = g.ekip_id
                WHERE g.kullanici_id = ?
                ORDER BY g.olusturma_tarihi DESC
                LIMIT ?
                """,
                (izleyen, izleyen, int(kullanici_id), int(limit)),
            )
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def feed_listele(kullanici_id: int, limit: int = 40) -> list[dict[str, Any]]:
        """Kendi, takip edilen ve üye olunan ekiplerin gönderileri."""
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT g.id, g.icerik, g.olusturma_tarihi, g.ekip_id, COALESCE(g.gorunurluk, 'herkes') AS gorunurluk,
                       u.id AS yazar_id, u.ad_soyad, u.kullanici_adi, u.avatar_yolu,
                       e.ad AS ekip_ad,
                       (SELECT COUNT(*) FROM Gonderi_Begeniler b WHERE b.gonderi_id = g.id) AS begeni_sayisi,
                       EXISTS(
                           SELECT 1 FROM Gonderi_Begeniler b2
                           WHERE b2.gonderi_id = g.id AND b2.kullanici_id = ?
                       ) AS begendim,
                       EXISTS(
                           SELECT 1 FROM Gonderi_Kayitlari k
                           WHERE k.gonderi_id = g.id AND k.kullanici_id = ?
                       ) AS kayitli
                FROM Gonderiler g
                JOIN Kullanicilar u ON u.id = g.kullanici_id
                LEFT JOIN Ekipler e ON e.id = g.ekip_id
                WHERE (
                    g.kullanici_id = ?
                    OR (
                        g.kullanici_id IN (
                            SELECT takip_edilen_id FROM Takipler WHERE takip_eden_id = ?
                        )
                        AND COALESCE(g.gorunurluk, 'herkes') IN ('herkes', 'baglanti')
                    )
                    OR (
                        g.ekip_id IN (
                            SELECT ekip_id FROM Ekip_Uyeleri WHERE kullanici_id = ?
                        )
                        AND COALESCE(g.gorunurluk, 'herkes') IN ('herkes', 'baglanti', 'ekip')
                    )
                )
                AND COALESCE(g.gorunurluk, 'herkes') != 'gizli'
                ORDER BY g.olusturma_tarihi DESC
                LIMIT ?
                """,
                (
                    int(kullanici_id),
                    int(kullanici_id),
                    int(kullanici_id),
                    int(kullanici_id),
                    int(kullanici_id),
                    int(kullanici_id),
                    int(limit),
                ),
            )
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def begeni_toggle(gonderi_id: int, kullanici_id: int) -> bool:
        """True = beğenildi, False = beğeni kaldırıldı."""
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT 1 FROM Gonderi_Begeniler WHERE gonderi_id = ? AND kullanici_id = ?",
                (int(gonderi_id), int(kullanici_id)),
            )
            if cur.fetchone():
                cur.execute(
                    "DELETE FROM Gonderi_Begeniler WHERE gonderi_id = ? AND kullanici_id = ?",
                    (int(gonderi_id), int(kullanici_id)),
                )
                conn.commit()
                return False
            cur.execute(
                "INSERT INTO Gonderi_Begeniler (gonderi_id, kullanici_id) VALUES (?, ?)",
                (int(gonderi_id), int(kullanici_id)),
            )
            conn.commit()
            return True
