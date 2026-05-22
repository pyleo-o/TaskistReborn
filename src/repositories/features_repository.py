# -*- coding: utf-8 -*-
"""features_repository.py — v4 özellikleri (DM, sprint, şablon, duyuru vb.)."""

from __future__ import annotations

import os
import shutil
from datetime import datetime
from typing import Any, Optional

import src.config as config
from src.db.connection import get_connection


class FeaturesRepository:
    # --- Presence ---
    @staticmethod
    def presence_guncelle(kullanici_id: int, cevrimici: bool = True) -> None:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE Kullanicilar
                SET son_gorulme = datetime('now'), cevrimici = ?
                WHERE id = ?
                """,
                (1 if cevrimici else 0, int(kullanici_id)),
            )
            conn.commit()

    @staticmethod
    def presence_getir(kullanici_id: int) -> dict[str, Any]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT son_gorulme, cevrimici FROM Kullanicilar WHERE id = ?",
                (int(kullanici_id),),
            )
            row = cur.fetchone()
            return dict(row) if row else {"son_gorulme": None, "cevrimici": 0}

    # --- Yetenekler ---
    @staticmethod
    def yetenekler_listele(kullanici_id: int) -> list[str]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT etiket FROM Kullanici_Yetenekleri WHERE kullanici_id = ? ORDER BY etiket",
                (int(kullanici_id),),
            )
            return [str(r["etiket"]) for r in cur.fetchall()]

    @staticmethod
    def yetenek_ekle(kullanici_id: int, etiket: str) -> None:
        et = (etiket or "").strip()[:40]
        if not et:
            return
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO Kullanici_Yetenekleri (kullanici_id, etiket) VALUES (?, ?)",
                (int(kullanici_id), et),
            )
            conn.commit()

    @staticmethod
    def yetenek_sil(kullanici_id: int, etiket: str) -> None:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM Kullanici_Yetenekleri WHERE kullanici_id = ? AND etiket = ?",
                (int(kullanici_id), (etiket or "").strip()),
            )
            conn.commit()

    # --- Bildirim tercihleri ---
    @staticmethod
    def bildirim_tercihleri_getir(kullanici_id: int) -> dict[str, int]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM Bildirim_Tercihleri WHERE kullanici_id = ?",
                (int(kullanici_id),),
            )
            row = cur.fetchone()
            if row:
                return dict(row)
            cur.execute(
                """
                INSERT INTO Bildirim_Tercihleri (kullanici_id) VALUES (?)
                """,
                (int(kullanici_id),),
            )
            conn.commit()
            return {
                "kullanici_id": int(kullanici_id),
                "gorev_atama": 1,
                "test_guncelleme": 1,
                "scrum": 1,
                "sosyal": 1,
                "dm": 1,
                "duyuru": 1,
            }

    @staticmethod
    def bildirim_tercihleri_kaydet(kullanici_id: int, tercihler: dict[str, int]) -> None:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO Bildirim_Tercihleri (
                    kullanici_id, gorev_atama, test_guncelleme, scrum, sosyal, dm, duyuru
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(kullanici_id) DO UPDATE SET
                    gorev_atama = excluded.gorev_atama,
                    test_guncelleme = excluded.test_guncelleme,
                    scrum = excluded.scrum,
                    sosyal = excluded.sosyal,
                    dm = excluded.dm,
                    duyuru = excluded.duyuru
                """,
                (
                    int(kullanici_id),
                    int(tercihler.get("gorev_atama", 1)),
                    int(tercihler.get("test_guncelleme", 1)),
                    int(tercihler.get("scrum", 1)),
                    int(tercihler.get("sosyal", 1)),
                    int(tercihler.get("dm", 1)),
                    int(tercihler.get("duyuru", 1)),
                ),
            )
            conn.commit()

    # --- Gönderi kaydet / görünürlük ---
    @staticmethod
    def gonderi_gorunurluk_guncelle(gonderi_id: int, gorunurluk: str) -> None:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE Gonderiler SET gorunurluk = ? WHERE id = ?",
                (gorunurluk, int(gonderi_id)),
            )
            conn.commit()

    @staticmethod
    def gonderi_kaydet_toggle(gonderi_id: int, kullanici_id: int) -> bool:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT 1 FROM Gonderi_Kayitlari WHERE gonderi_id = ? AND kullanici_id = ?",
                (int(gonderi_id), int(kullanici_id)),
            )
            if cur.fetchone():
                cur.execute(
                    "DELETE FROM Gonderi_Kayitlari WHERE gonderi_id = ? AND kullanici_id = ?",
                    (int(gonderi_id), int(kullanici_id)),
                )
                conn.commit()
                return False
            cur.execute(
                "INSERT INTO Gonderi_Kayitlari (gonderi_id, kullanici_id) VALUES (?, ?)",
                (int(gonderi_id), int(kullanici_id)),
            )
            conn.commit()
            return True

    @staticmethod
    def kayitli_gonderiler(kullanici_id: int, limit: int = 50) -> list[dict[str, Any]]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT g.id, g.icerik, g.olusturma_tarihi, g.gorunurluk,
                       u.ad_soyad, u.kullanici_adi
                FROM Gonderi_Kayitlari k
                JOIN Gonderiler g ON g.id = k.gonderi_id
                JOIN Kullanicilar u ON u.id = g.kullanici_id
                WHERE k.kullanici_id = ?
                ORDER BY k.tarih DESC
                LIMIT ?
                """,
                (int(kullanici_id), int(limit)),
            )
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def baglanti_onerileri(kullanici_id: int, limit: int = 8) -> list[dict[str, Any]]:
        """Takip etmediğiniz; ortak takip / ekip bağlantısı olan kullanıcılar."""
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT k.id, k.ad_soyad, k.kullanici_adi, k.email, k.avatar_yolu,
                       k.cevrimici, k.son_gorulme,
                       (
                           SELECT COUNT(*) FROM Takipler t1
                           JOIN Takipler t2 ON t1.takip_edilen_id = t2.takip_eden_id
                           WHERE t1.takip_eden_id = ? AND t2.takip_edilen_id = k.id
                       ) AS ortak_takip
                FROM Kullanicilar k
                WHERE k.id != ?
                  AND k.id NOT IN (
                      SELECT takip_edilen_id FROM Takipler WHERE takip_eden_id = ?
                  )
                  AND COALESCE(k.profil_gizli, 0) = 0
                ORDER BY ortak_takip DESC, k.olusturma_tarihi DESC
                LIMIT ?
                """,
                (int(kullanici_id), int(kullanici_id), int(kullanici_id), int(limit)),
            )
            return [dict(r) for r in cur.fetchall()]

    # --- DM ---
    @staticmethod
    def sohbet_bul_veya_olustur(k1: int, k2: int) -> int:
        if int(k1) == int(k2):
            raise ValueError("Kendinize mesaj gönderemezsiniz.")
        a, b = sorted((int(k1), int(k2)))
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT s.id FROM Sohbetler s
                JOIN Sohbet_Uyeleri u1 ON u1.sohbet_id = s.id AND u1.kullanici_id = ?
                JOIN Sohbet_Uyeleri u2 ON u2.sohbet_id = s.id AND u2.kullanici_id = ?
                LIMIT 1
                """,
                (a, b),
            )
            row = cur.fetchone()
            if row:
                return int(row["id"])
            cur.execute("INSERT INTO Sohbetler DEFAULT VALUES")
            sid = int(cur.lastrowid)
            cur.execute(
                "INSERT INTO Sohbet_Uyeleri (sohbet_id, kullanici_id) VALUES (?, ?), (?, ?)",
                (sid, a, sid, b),
            )
            conn.commit()
            return sid

    @staticmethod
    def mesaj_gonder(sohbet_id: int, gonderen_id: int, icerik: str) -> int:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO Mesajlar (sohbet_id, gonderen_id, icerik) VALUES (?, ?, ?)",
                (int(sohbet_id), int(gonderen_id), (icerik or "").strip()),
            )
            conn.commit()
            return int(cur.lastrowid)

    @staticmethod
    def sohbet_listesi(kullanici_id: int) -> list[dict[str, Any]]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT s.id AS sohbet_id,
                       diger.id AS karsi_id,
                       diger.ad_soyad, diger.kullanici_adi, diger.avatar_yolu,
                       diger.cevrimici, diger.son_gorulme,
                       (SELECT icerik FROM Mesajlar m
                        WHERE m.sohbet_id = s.id ORDER BY m.tarih DESC LIMIT 1) AS son_mesaj,
                       (SELECT tarih FROM Mesajlar m
                        WHERE m.sohbet_id = s.id ORDER BY m.tarih DESC LIMIT 1) AS son_tarih
                FROM Sohbetler s
                JOIN Sohbet_Uyeleri ben ON ben.sohbet_id = s.id AND ben.kullanici_id = ?
                JOIN Sohbet_Uyeleri o ON o.sohbet_id = s.id AND o.kullanici_id != ?
                JOIN Kullanicilar diger ON diger.id = o.kullanici_id
                ORDER BY son_tarih IS NULL, son_tarih DESC
                """,
                (int(kullanici_id), int(kullanici_id)),
            )
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def mesajlari_listele(sohbet_id: int, limit: int = 80) -> list[dict[str, Any]]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT m.*, u.ad_soyad, u.kullanici_adi
                FROM Mesajlar m
                JOIN Kullanicilar u ON u.id = m.gonderen_id
                WHERE m.sohbet_id = ?
                ORDER BY m.tarih ASC
                LIMIT ?
                """,
                (int(sohbet_id), int(limit)),
            )
            return [dict(r) for r in cur.fetchall()]

    # --- Sprint ---
    @staticmethod
    def sprint_ekle(ekip_id: int, ad: str, hedef: str, baslangic: str, bitis: str) -> int:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO Sprintler (ekip_id, ad, hedef, baslangic, bitis, durum)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    int(ekip_id),
                    (ad or "").strip(),
                    (hedef or "").strip(),
                    baslangic or None,
                    bitis or None,
                    config.SPRINT_DURUM_AKTIF,
                ),
            )
            conn.commit()
            return int(cur.lastrowid)

    @staticmethod
    def sprintler_listele(ekip_id: int) -> list[dict[str, Any]]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT s.*,
                       (SELECT COUNT(*) FROM Gorevler g WHERE g.sprint_id = s.id) AS gorev_sayisi
                FROM Sprintler s
                WHERE s.ekip_id = ?
                ORDER BY s.olusturma_tarihi DESC
                """,
                (int(ekip_id),),
            )
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def gorev_sprint_ata(gorev_id: int, sprint_id: Optional[int]) -> None:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE Gorevler SET sprint_id = ? WHERE id = ?",
                (sprint_id, int(gorev_id)),
            )
            conn.commit()

    # --- Şablon ---
    @staticmethod
    def sablon_ekle(ekip_id: int, baslik: str, aciklama: str, kritiklik: str, olusturan_id: int) -> int:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO Gorev_Sablonlari (ekip_id, baslik, aciklama, kritiklik, olusturan_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (int(ekip_id), baslik.strip(), (aciklama or "").strip(), kritiklik, int(olusturan_id)),
            )
            conn.commit()
            return int(cur.lastrowid)

    @staticmethod
    def sablonlar_listele(ekip_id: int) -> list[dict[str, Any]]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM Gorev_Sablonlari WHERE ekip_id = ? ORDER BY olusturma_tarihi DESC",
                (int(ekip_id),),
            )
            return [dict(r) for r in cur.fetchall()]

    # --- Görev ek / aktivite / durum ---
    @staticmethod
    def gorev_durum_guncelle(gorev_id: int, yeni_durum: str) -> None:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE Gorevler SET durum = ? WHERE id = ?", (yeni_durum, int(gorev_id)))
            conn.commit()

    @staticmethod
    def gorev_aktivite_ekle(
        gorev_id: int,
        islem: str,
        detay: str = "",
        kullanici_id: Optional[int] = None,
        ekip_id: Optional[int] = None,
    ) -> None:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO Gorev_Aktivite (gorev_id, kullanici_id, ekip_id, islem, detay)
                VALUES (?, ?, ?, ?, ?)
                """,
                (int(gorev_id), kullanici_id, ekip_id, islem, (detay or "")[:500]),
            )
            conn.commit()

    @staticmethod
    def gorev_aktivite_listele(gorev_id: int, limit: int = 40) -> list[dict[str, Any]]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT a.*, u.ad_soyad, u.kullanici_adi
                FROM Gorev_Aktivite a
                LEFT JOIN Kullanicilar u ON u.id = a.kullanici_id
                WHERE a.gorev_id = ?
                ORDER BY a.tarih DESC
                LIMIT ?
                """,
                (int(gorev_id), int(limit)),
            )
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def gorev_ek_ekle(gorev_id: int, kaynak_dosya: str, dosya_adi: str, yukleyen_id: int) -> int:
        os.makedirs(config.EKLER_DIR, exist_ok=True)
        ext = os.path.splitext(dosya_adi)[1]
        hedef_ad = f"g{gorev_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{yukleyen_id}{ext}"
        hedef = os.path.join(config.EKLER_DIR, hedef_ad)
        shutil.copy2(kaynak_dosya, hedef)
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO Gorev_Ekleri (gorev_id, dosya_yolu, dosya_adi, yukleyen_id)
                VALUES (?, ?, ?, ?)
                """,
                (int(gorev_id), hedef, dosya_adi, int(yukleyen_id)),
            )
            conn.commit()
            return int(cur.lastrowid)

    @staticmethod
    def gorev_ekleri_listele(gorev_id: int) -> list[dict[str, Any]]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM Gorev_Ekleri WHERE gorev_id = ? ORDER BY tarih DESC",
                (int(gorev_id),),
            )
            return [dict(r) for r in cur.fetchall()]

    # --- Duyuru ---
    @staticmethod
    def duyuru_ekle(ekip_id: int, yazar_id: int, baslik: str, icerik: str, sabit: bool = False) -> int:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO Ekip_Duyurulari (ekip_id, yazar_id, baslik, icerik, sabit)
                VALUES (?, ?, ?, ?, ?)
                """,
                (int(ekip_id), int(yazar_id), baslik.strip(), icerik.strip(), 1 if sabit else 0),
            )
            conn.commit()
            return int(cur.lastrowid)

    @staticmethod
    def duyurular_listele(ekip_id: int, limit: int = 20) -> list[dict[str, Any]]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT d.*, u.ad_soyad, u.kullanici_adi
                FROM Ekip_Duyurulari d
                JOIN Kullanicilar u ON u.id = d.yazar_id
                WHERE d.ekip_id = ?
                ORDER BY d.sabit DESC, d.olusturma_tarihi DESC
                LIMIT ?
                """,
                (int(ekip_id), int(limit)),
            )
            return [dict(r) for r in cur.fetchall()]

    # --- Dashboard özet / sağlık ---
    @staticmethod
    def ekip_gorev_ozeti(ekip_id: int) -> dict[str, int]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT durum, COUNT(*) AS c FROM Gorevler
                WHERE ekip_id = ? GROUP BY durum
                """,
                (int(ekip_id),),
            )
            ozet = {str(r["durum"]): int(r["c"]) for r in cur.fetchall()}
            cur.execute("SELECT COUNT(*) AS c FROM Gorevler WHERE ekip_id = ?", (int(ekip_id),))
            toplam = int(cur.fetchone()["c"])
            return {"toplam": toplam, "durumlar": ozet}

    @staticmethod
    def ekip_saglik_skoru(ekip_id: int) -> dict[str, Any]:
        oz = FeaturesRepository.ekip_gorev_ozeti(ekip_id)
        toplam = max(oz.get("toplam", 0), 1)
        durumlar = oz.get("durumlar") or {}
        tamam = int(durumlar.get(config.DURUM_TAMAMLANDI, 0))
        revize = int(durumlar.get(config.DURUM_REVIZYON, 0))
        kritik = 0
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT COUNT(*) AS c FROM Gorevler
                WHERE ekip_id = ? AND kritiklik = ? AND durum != ?
                """,
                (int(ekip_id), config.ONCELIK_KRITIK, config.DURUM_TAMAMLANDI),
            )
            kritik = int(cur.fetchone()["c"])
        tamamlanma_orani = tamam / toplam
        revize_cezasi = min(revize * 8, 40)
        kritik_cezasi = min(kritik * 10, 30)
        skor = int(max(0, min(100, tamamlanma_orani * 70 + 30 - revize_cezasi - kritik_cezasi)))
        return {
            "skor": skor,
            "tamamlanan": tamam,
            "toplam": oz.get("toplam", 0),
            "revize": revize,
            "acik_kritik": kritik,
        }
