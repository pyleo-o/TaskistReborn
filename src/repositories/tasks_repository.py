# -*- coding: utf-8 -*-
"""
tasks_repository.py — Gorevler ve AltGorevler tablolarına erişim.

Sorgular ekip (workspace) bağlamına göre filtrelenir; böylece yönetici yalnızca
seçtiği çalışma alanındaki kartları görür.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import src.config as config
from src.db.connection import get_connection


class TasksRepository:
    """Görev ve alt görev satırları."""

    @staticmethod
    def ekipteki_gelistirici_uyeler(ekip_id: int) -> list[dict[str, Any]]:
        """
        Görev atanabilecek ekip üyeleri: Backend, Frontend, Sistem Analisti rolleri.

        Tester ve Yönetici bu listede yer almaz (rapor: yazılımcıya atama).
        """
        roller = (config.ROL_BACKEND, config.ROL_FRONTEND, config.ROL_SISTEM_ANALISTI)
        placeholders = ",".join("?" * len(roller))
        sql = f"""
            SELECT
                k.id AS kullanici_id,
                k.email,
                k.ad_soyad,
                r.rol_adi AS rol_adi
            FROM Ekip_Uyeleri eu
            JOIN Kullanicilar k ON k.id = eu.kullanici_id
            JOIN Roller r ON r.id = eu.rol_id
            WHERE eu.ekip_id = ?
              AND r.rol_adi IN ({placeholders})
            ORDER BY COALESCE(NULLIF(TRIM(k.ad_soyad), ''), k.email) COLLATE NOCASE
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (int(ekip_id),) + roller)
            return [dict(row) for row in cur.fetchall()]

    @staticmethod
    def ekip_gorevlerini_listele(ekip_id: int) -> list[dict[str, Any]]:
        """
        Ekip görevlerini döndürür; kritiklik 'Kritik' olanlar önce gelecek şekilde sıralanır.

        Dönüş alanları: gorev satırı + atanan e-posta/ad + alt görev sayısı (opsiyonel).
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                f"""
                SELECT
                    g.id,
                    g.ekip_id,
                    g.baslik,
                    g.aciklama,
                    g.kritiklik,
                    g.durum,
                    g.olusturan_kullanici_id,
                    g.atanan_kullanici_id,
                    g.due_date,
                    g.revize_kritikligi,
                    g.atama_zamani,
                    g.tamamlanma_zamani,
                    g.olusturma_tarihi,
                    a.email AS atanan_email,
                    COALESCE(NULLIF(TRIM(a.ad_soyad), ''), a.email) AS atanan_gosterim,
                    o.email AS olusturan_email
                FROM Gorevler g
                LEFT JOIN Kullanicilar a ON a.id = g.atanan_kullanici_id
                JOIN Kullanicilar o ON o.id = g.olusturan_kullanici_id
                WHERE g.ekip_id = ?
                ORDER BY
                    CASE WHEN g.kritiklik = ? THEN 0 ELSE 1 END,
                    g.olusturma_tarihi DESC
                """,
                (int(ekip_id), config.ONCELIK_KRITIK),
            )
            return [dict(row) for row in cur.fetchall()]

    @staticmethod
    def gorev_ekle(
        ekip_id: int,
        baslik: str,
        aciklama: str,
        kritiklik: str,
        olusturan_kullanici_id: int,
        atanan_kullanici_id: int,
        due_date: Optional[str],
    ) -> int:
        """Yeni görev satırı ekler; yeni id döner."""
        atama = datetime.now().isoformat(timespec="seconds")
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO Gorevler (
                    ekip_id, baslik, aciklama, kritiklik, durum,
                    olusturan_kullanici_id, atanan_kullanici_id, due_date,
                    atama_zamani
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(ekip_id),
                    baslik,
                    aciklama,
                    kritiklik,
                    config.DURUM_BEKLEMEDE,
                    int(olusturan_kullanici_id),
                    int(atanan_kullanici_id),
                    due_date,
                    atama,
                ),
            )
            conn.commit()
            return int(cur.lastrowid)

    @staticmethod
    def alt_gorevleri_listele(gorev_id: int) -> list[dict[str, Any]]:
        """Bir göreve bağlı alt görevleri sıra numarasına göre listeler."""
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, gorev_id, baslik, tamamlandi, sira
                FROM AltGorevler
                WHERE gorev_id = ?
                ORDER BY sira ASC, id ASC
                """,
                (int(gorev_id),),
            )
            return [dict(row) for row in cur.fetchall()]

    @staticmethod
    def alt_gorev_ekle(gorev_id: int, baslik: str) -> int:
        """Yeni alt görev ekler; sira = mevcut max + 1."""
        baslik = baslik.strip()
        if not baslik:
            raise ValueError("Alt görev başlığı boş olamaz.")

        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT COALESCE(MAX(sira), 0) AS m FROM AltGorevler WHERE gorev_id = ?",
                (int(gorev_id),),
            )
            sira = int(cur.fetchone()["m"]) + 1
            cur.execute(
                """
                INSERT INTO AltGorevler (gorev_id, baslik, tamamlandi, sira)
                VALUES (?, ?, 0, ?)
                """,
                (int(gorev_id), baslik, sira),
            )
            conn.commit()
            return int(cur.lastrowid)

    @staticmethod
    def alt_gorev_tamamlandi_guncelle(alt_gorev_id: int, tamamlandi: bool) -> None:
        """Checkbox durumunu veritabanına yazar."""
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE AltGorevler
                SET tamamlandi = ?
                WHERE id = ?
                """,
                (1 if tamamlandi else 0, int(alt_gorev_id)),
            )
            conn.commit()

    @staticmethod
    def gorev_getir(gorev_id: int) -> Optional[dict[str, Any]]:
        """Tek görev satırı (yetki kontrolleri için)."""
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM Gorevler WHERE id = ? LIMIT 1", (int(gorev_id),))
            row = cur.fetchone()
            return dict(row) if row else None

    @staticmethod
    def gelistirici_beklemede_ve_revizyon(ekip_id: int, kullanici_id: int) -> list[dict[str, Any]]:
        """
        Yazılımcı paneli: kendisine atanmış Beklemede veya Revizyon görevleri.

        Revizyon (iade) kartları üstte; kritik revize etiketi önceliklidir.
        """
        durumlar = (config.DURUM_BEKLEMEDE, config.DURUM_REVIZYON)
        ph = ",".join("?" * len(durumlar))
        sql = f"""
            SELECT
                g.id,
                g.ekip_id,
                g.baslik,
                g.aciklama,
                g.kritiklik,
                g.durum,
                g.due_date,
                g.revize_kritikligi,
                g.kod_metni,
                g.son_tarama_ozeti,
                g.atama_zamani,
                g.olusturma_tarihi
            FROM Gorevler g
            WHERE g.ekip_id = ?
              AND g.atanan_kullanici_id = ?
              AND g.durum IN ({ph})
            ORDER BY
                CASE WHEN g.durum = ? THEN 0 ELSE 1 END,
                CASE WHEN g.revize_kritikligi = ? THEN 0 ELSE 1 END,
                g.olusturma_tarihi DESC
        """
        params = (int(ekip_id), int(kullanici_id)) + durumlar + (config.DURUM_REVIZYON, config.ONCELIK_KRITIK)
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def ekip_testteki_gorevler(ekip_id: int) -> list[dict[str, Any]]:
        """Tester: ekibin test aşamasındaki görevleri (kritiklik sıralı)."""
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                f"""
                SELECT
                    g.id,
                    g.ekip_id,
                    g.baslik,
                    g.aciklama,
                    g.kritiklik,
                    g.durum,
                    g.due_date,
                    g.revize_kritikligi,
                    g.kod_metni,
                    g.son_tarama_ozeti,
                    g.atama_zamani,
                    g.atanan_kullanici_id,
                    COALESCE(NULLIF(TRIM(a.ad_soyad), ''), a.email) AS atanan_gosterim
                FROM Gorevler g
                LEFT JOIN Kullanicilar a ON a.id = g.atanan_kullanici_id
                WHERE g.ekip_id = ? AND g.durum = ?
                ORDER BY
                    CASE WHEN g.kritiklik = ? THEN 0 ELSE 1 END,
                    g.olusturma_tarihi DESC
                """,
                (int(ekip_id), config.DURUM_TESTTE, config.ONCELIK_KRITIK),
            )
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def gorev_kodu_yukle_ve_teste_gonder(
        gorev_id: int,
        kullanici_id: int,
        kod_metni: str,
        tarama_ozeti: str,
    ) -> None:
        """
        Yazılımcı kodu yükler; durum 'Test Aşamasına' alınır.

        Yalnızca atanan kullanıcı ve Beklemede/Revizyon durumlarında çalışır.
        """
        kod_metni = (kod_metni or "").strip()
        if not kod_metni:
            raise ValueError("Kod alanı boş olamaz.")

        with get_connection() as conn:
            try:
                conn.execute("PRAGMA foreign_keys = ON")
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, atanan_kullanici_id, durum FROM Gorevler WHERE id = ? LIMIT 1",
                    (int(gorev_id),),
                )
                row = cur.fetchone()
                if row is None:
                    raise ValueError("Görev bulunamadı.")
                if int(row["atanan_kullanici_id"] or 0) != int(kullanici_id):
                    raise PermissionError("Bu görev size atanmamış.")
                izin = (
                    config.DURUM_BEKLEMEDE,
                    config.DURUM_REVIZYON,
                    config.DURUM_KODLANIYOR,
                    config.DURUM_KOD_INCELEMEDE,
                )
                if str(row["durum"]) not in izin:
                    raise ValueError("Bu görev bu aşamada kod yüklemesi kabul etmiyor.")

                cur.execute(
                    """
                    UPDATE Gorevler
                    SET kod_metni = ?,
                        son_tarama_ozeti = ?,
                        durum = ?
                    WHERE id = ?
                    """,
                    (kod_metni, (tarama_ozeti or "").strip(), config.DURUM_TESTTE, int(gorev_id)),
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    @staticmethod
    def islem_log_ekle(
        kullanici_id: Optional[int],
        ekip_id: Optional[int],
        gorev_id: Optional[int],
        islem_tipi: str,
        detay: str,
        sure_saniye: Optional[int] = None,
    ) -> None:
        """Islem_Loglari tablosuna satır ekler (süre analizi için)."""
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO Islem_Loglari (kullanici_id, ekip_id, gorev_id, islem_tipi, detay, sure_saniye)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    kullanici_id,
                    ekip_id,
                    gorev_id,
                    islem_tipi,
                    detay,
                    sure_saniye,
                ),
            )
            conn.commit()

    @staticmethod
    def gorev_onayla_tamamla(
        gorev_id: int,
        tester_kullanici_id: int,
        ekip_id: int,
    ) -> int:
        """
        Tester onayı: görev Tamamlandı + tamamlanma zamanı + süre logu.

        Returns:
            Kaydedilen süre (saniye).
        """
        from datetime import datetime

        with get_connection() as conn:
            try:
                conn.execute("PRAGMA foreign_keys = ON")
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT id, durum, atama_zamani
                    FROM Gorevler
                    WHERE id = ? AND ekip_id = ?
                    LIMIT 1
                    """,
                    (int(gorev_id), int(ekip_id)),
                )
                row = cur.fetchone()
                if row is None:
                    raise ValueError("Görev bulunamadı veya ekip uyuşmuyor.")
                if str(row["durum"]) != config.DURUM_TESTTE:
                    raise ValueError("Yalnızca test aşamasındaki görevler onaylanabilir.")

                bitis = datetime.now().isoformat(timespec="seconds")
                sure = 0
                atama = row["atama_zamani"]
                if atama:
                    try:
                        bas = datetime.fromisoformat(str(atama))
                        sure = max(0, int((datetime.fromisoformat(bitis) - bas).total_seconds()))
                    except Exception:
                        sure = 0

                cur.execute(
                    """
                    UPDATE Gorevler
                    SET durum = ?, tamamlanma_zamani = ?
                    WHERE id = ?
                    """,
                    (config.DURUM_TAMAMLANDI, bitis, int(gorev_id)),
                )
                cur.execute(
                    """
                    INSERT INTO Islem_Loglari (kullanici_id, ekip_id, gorev_id, islem_tipi, detay, sure_saniye)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        int(tester_kullanici_id),
                        int(ekip_id),
                        int(gorev_id),
                        "GOREV_ONAY_TAMAMLANDI",
                        f"Tester onayı ile tamamlandı. Bitiş: {bitis}",
                        int(sure),
                    ),
                )
                conn.commit()
                return int(sure)
            except Exception:
                conn.rollback()
                raise

    @staticmethod
    def gorev_revizeye_gonder(
        gorev_id: int,
        tester_kullanici_id: int,
        ekip_id: int,
        revize_kritikligi: str,
    ) -> None:
        """Tester revizyon: durum Revizyon + matris seviyesi revize_kritikligi alanına yazılır."""
        if revize_kritikligi not in config.KRITIKLIK_SECENEKLERI:
            raise ValueError("Geçersiz kritiklik matrisi.")

        with get_connection() as conn:
            try:
                conn.execute("PRAGMA foreign_keys = ON")
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, durum FROM Gorevler WHERE id = ? AND ekip_id = ? LIMIT 1",
                    (int(gorev_id), int(ekip_id)),
                )
                row = cur.fetchone()
                if row is None:
                    raise ValueError("Görev bulunamadı.")
                if str(row["durum"]) != config.DURUM_TESTTE:
                    raise ValueError("Yalnızca testteki görevler revizeye gönderilebilir.")

                cur.execute(
                    """
                    UPDATE Gorevler
                    SET durum = ?, revize_kritikligi = ?
                    WHERE id = ?
                    """,
                    (config.DURUM_REVIZYON, revize_kritikligi, int(gorev_id)),
                )
                cur.execute(
                    """
                    INSERT INTO Islem_Loglari (kullanici_id, ekip_id, gorev_id, islem_tipi, detay, sure_saniye)
                    VALUES (?, ?, ?, ?, ?, NULL)
                    """,
                    (
                        int(tester_kullanici_id),
                        int(ekip_id),
                        int(gorev_id),
                        "GOREV_REVIZE_ISTENDI",
                        f"Revize matrisi: {revize_kritikligi}",
                    ),
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    @staticmethod
    def ekip_islem_loglari(ekip_id: int, limit: int = 200) -> list[dict[str, Any]]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT l.*, COALESCE(NULLIF(TRIM(k.ad_soyad), ''), k.email) AS kullanici_gosterim
                FROM Islem_Loglari l
                LEFT JOIN Kullanicilar k ON k.id = l.kullanici_id
                WHERE l.ekip_id = ?
                ORDER BY l.tarih DESC
                LIMIT ?
                """,
                (int(ekip_id), int(limit)),
            )
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def ekip_tamamlanan_sure_raporu(ekip_id: int) -> list[dict[str, Any]]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT g.id AS gorev_id, g.baslik, g.kritiklik, g.tamamlanma_zamani,
                       l.sure_saniye,
                       COALESCE(NULLIF(TRIM(a.ad_soyad), ''), a.email) AS atanan_gosterim,
                       g.atanan_kullanici_id
                FROM Gorevler g
                LEFT JOIN Islem_Loglari l ON l.gorev_id = g.id AND l.islem_tipi = 'GOREV_ONAY_TAMAMLANDI'
                LEFT JOIN Kullanicilar a ON a.id = g.atanan_kullanici_id
                WHERE g.ekip_id = ? AND g.durum = ?
                ORDER BY l.sure_saniye DESC
                """,
                (int(ekip_id), config.DURUM_TAMAMLANDI),
            )
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def ekip_uye_performans_ozeti(ekip_id: int) -> list[dict[str, Any]]:
        """Tamamlanan görevlere göre ekip üyesi bazında süre özeti (ekip performans takibi)."""
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    g.atanan_kullanici_id AS kullanici_id,
                    COALESCE(NULLIF(TRIM(a.ad_soyad), ''), a.email) AS uye_gosterim,
                    COUNT(*) AS tamamlanan_adet,
                    AVG(l.sure_saniye) AS ortalama_saniye,
                    SUM(l.sure_saniye) AS toplam_saniye
                FROM Gorevler g
                INNER JOIN Islem_Loglari l
                    ON l.gorev_id = g.id AND l.islem_tipi = 'GOREV_ONAY_TAMAMLANDI'
                LEFT JOIN Kullanicilar a ON a.id = g.atanan_kullanici_id
                WHERE g.ekip_id = ? AND g.durum = ? AND g.atanan_kullanici_id IS NOT NULL
                GROUP BY g.atanan_kullanici_id
                ORDER BY tamamlanan_adet DESC, ortalama_saniye ASC
                """,
                (int(ekip_id), config.DURUM_TAMAMLANDI),
            )
            rows = []
            for row in cur.fetchall():
                d = dict(row)
                d["ortalama_saniye"] = int(d.get("ortalama_saniye") or 0)
                d["toplam_saniye"] = int(d.get("toplam_saniye") or 0)
                d["tamamlanan_adet"] = int(d.get("tamamlanan_adet") or 0)
                rows.append(d)
            return rows

    @staticmethod
    def gorev_guncelle(
        gorev_id: int,
        ekip_id: int,
        baslik: str,
        aciklama: str,
        kritiklik: str,
        due_date: Optional[str],
        atanan_kullanici_id: Optional[int] = None,
    ) -> None:
        with get_connection() as conn:
            cur = conn.cursor()
            if atanan_kullanici_id is not None:
                cur.execute(
                    """
                    UPDATE Gorevler
                    SET baslik = ?, aciklama = ?, kritiklik = ?, due_date = ?, atanan_kullanici_id = ?
                    WHERE id = ? AND ekip_id = ?
                    """,
                    (
                        baslik,
                        aciklama,
                        kritiklik,
                        due_date,
                        int(atanan_kullanici_id),
                        int(gorev_id),
                        int(ekip_id),
                    ),
                )
            else:
                cur.execute(
                    """
                    UPDATE Gorevler
                    SET baslik = ?, aciklama = ?, kritiklik = ?, due_date = ?
                    WHERE id = ? AND ekip_id = ?
                    """,
                    (baslik, aciklama, kritiklik, due_date, int(gorev_id), int(ekip_id)),
                )
            conn.commit()

    @staticmethod
    def gorev_sil(gorev_id: int, ekip_id: int) -> None:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM Gorevler WHERE id = ? AND ekip_id = ?", (int(gorev_id), int(ekip_id)))
            conn.commit()

    @staticmethod
    def gorev_ustlen(gorev_id: int, kullanici_id: int) -> None:
        from datetime import datetime

        atama = datetime.now().isoformat(timespec="seconds")
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT atanan_kullanici_id, durum FROM Gorevler WHERE id = ? LIMIT 1",
                (int(gorev_id),),
            )
            row = cur.fetchone()
            if row is None:
                raise ValueError("Görev bulunamadı.")
            if int(row["atanan_kullanici_id"] or 0) != int(kullanici_id):
                raise PermissionError("Bu görev size atanmamış.")
            if str(row["durum"]) != config.DURUM_BEKLEMEDE:
                raise ValueError("Yalnızca beklemedeki görevler üstlenilebilir.")
            cur.execute(
                "UPDATE Gorevler SET durum = ?, atama_zamani = ? WHERE id = ?",
                (config.DURUM_KODLANIYOR, atama, int(gorev_id)),
            )
            conn.commit()

    @staticmethod
    def gorev_kod_incelemede(
        gorev_id: int,
        kullanici_id: int,
        kod_metni: str,
        tarama_ozeti: str,
    ) -> None:
        kod_metni = (kod_metni or "").strip()
        if not kod_metni:
            raise ValueError("Kod alanı boş olamaz.")
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT atanan_kullanici_id, durum FROM Gorevler WHERE id = ? LIMIT 1",
                (int(gorev_id),),
            )
            row = cur.fetchone()
            if row is None:
                raise ValueError("Görev bulunamadı.")
            if int(row["atanan_kullanici_id"] or 0) != int(kullanici_id):
                raise PermissionError("Bu görev size atanmamış.")
            izin = (
                config.DURUM_BEKLEMEDE,
                config.DURUM_REVIZYON,
                config.DURUM_KODLANIYOR,
                config.DURUM_KOD_INCELEMEDE,
            )
            if str(row["durum"]) not in izin:
                raise ValueError("Bu görev bu aşamada kod yüklemesi kabul etmiyor.")
            cur.execute(
                """
                UPDATE Gorevler
                SET kod_metni = ?, son_tarama_ozeti = ?, durum = ?
                WHERE id = ?
                """,
                (kod_metni, tarama_ozeti, config.DURUM_KOD_INCELEMEDE, int(gorev_id)),
            )
            conn.commit()

    @staticmethod
    def gorev_tarayici_revizyon(
        gorev_id: int,
        kullanici_id: int,
        kod_metni: str,
        tarama_ozeti: str,
    ) -> None:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE Gorevler
                SET kod_metni = ?, son_tarama_ozeti = ?, durum = ?
                WHERE id = ? AND atanan_kullanici_id = ?
                """,
                (kod_metni, tarama_ozeti, config.DURUM_REVIZYON, int(gorev_id), int(kullanici_id)),
            )
            conn.commit()

    @staticmethod
    def gorev_teste_zorla(gorev_id: int, kullanici_id: int, kod_metni: str, tarama_ozeti: str) -> None:
        kod_metni = (kod_metni or "").strip()
        if not kod_metni:
            raise ValueError("Kod alanı boş olamaz.")
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE Gorevler
                SET kod_metni = ?, son_tarama_ozeti = ?, durum = ?
                WHERE id = ? AND atanan_kullanici_id = ?
                """,
                (kod_metni, tarama_ozeti, config.DURUM_TESTTE, int(gorev_id), int(kullanici_id)),
            )
            conn.commit()

    @staticmethod
    def gelistirici_acik_gorevler(ekip_id: int, kullanici_id: int) -> list[dict[str, Any]]:
        durumlar = (
            config.DURUM_BEKLEMEDE,
            config.DURUM_REVIZYON,
            config.DURUM_KODLANIYOR,
            config.DURUM_KOD_INCELEMEDE,
        )
        ph = ",".join("?" * len(durumlar))
        sql = f"""
            SELECT g.* FROM Gorevler g
            WHERE g.ekip_id = ? AND g.atanan_kullanici_id = ? AND g.durum IN ({ph})
            ORDER BY
                CASE WHEN g.durum = ? THEN 0 ELSE 1 END,
                CASE WHEN g.revize_kritikligi = ? THEN 0 ELSE 1 END,
                g.olusturma_tarihi DESC
        """
        params = (int(ekip_id), int(kullanici_id)) + durumlar + (
            config.DURUM_REVIZYON,
            config.ONCELIK_KRITIK,
        )
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def atanan_aktif_gorev_sayisi_ekipte(ekip_id: int, kullanici_id: int) -> int:
        """Tamamlanmamış, bu ekipte atanan görev sayısı (yoğunluk uyarısı için)."""
        durumlar = (
            config.DURUM_BEKLEMEDE,
            config.DURUM_KODLANIYOR,
            config.DURUM_KOD_INCELEMEDE,
            config.DURUM_TESTTE,
            config.DURUM_REVIZYON,
        )
        ph = ",".join("?" * len(durumlar))
        sql = f"""
            SELECT COUNT(*) AS c FROM Gorevler
            WHERE ekip_id = ? AND atanan_kullanici_id = ? AND durum IN ({ph})
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (int(ekip_id), int(kullanici_id)) + durumlar)
            return int(cur.fetchone()["c"])

    @staticmethod
    def kullanici_gorev_istatistik(kullanici_id: int) -> dict[str, int]:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) AS c FROM Gorevler WHERE atanan_kullanici_id = ? AND durum = ?",
                (int(kullanici_id), config.DURUM_TAMAMLANDI),
            )
            tamam = int(cur.fetchone()["c"])
            cur.execute(
                "SELECT COUNT(*) AS c FROM Gorevler WHERE atanan_kullanici_id = ? AND durum != ?",
                (int(kullanici_id), config.DURUM_TAMAMLANDI),
            )
            aktif = int(cur.fetchone()["c"])
            return {"tamamlanan": tamam, "aktif": aktif}
