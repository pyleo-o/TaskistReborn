# -*- coding: utf-8 -*-
"""migrations.py — Şema sürüm yükseltmeleri (mevcut DB'ye zarar vermeden)."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def _kolon_var_mi(cur, tablo: str, kolon: str) -> bool:
    cur.execute(f"PRAGMA table_info({tablo})")
    return any(row[1] == kolon for row in cur.fetchall())


def migrate_v2(conn) -> None:
    """Profil, takip ve tema tercihi alanları."""
    cur = conn.cursor()
    kolonlar = [
        ("kullanici_adi", "TEXT"),
        ("bio", "TEXT NOT NULL DEFAULT ''"),
        ("profil_gizli", "INTEGER NOT NULL DEFAULT 0"),
        ("avatar_yolu", "TEXT"),
        ("tercih_tema", "TEXT NOT NULL DEFAULT 'dark'"),
    ]
    for ad, tip in kolonlar:
        if not _kolon_var_mi(cur, "Kullanicilar", ad):
            cur.execute(f"ALTER TABLE Kullanicilar ADD COLUMN {ad} {tip}")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Takipler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            takip_eden_id INTEGER NOT NULL,
            takip_edilen_id INTEGER NOT NULL,
            tarih TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE (takip_eden_id, takip_edilen_id),
            FOREIGN KEY (takip_eden_id) REFERENCES Kullanicilar(id) ON DELETE CASCADE,
            FOREIGN KEY (takip_edilen_id) REFERENCES Kullanicilar(id) ON DELETE CASCADE
        )
        """
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_takipler_eden ON Takipler(takip_eden_id)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_takipler_edilen ON Takipler(takip_edilen_id)"
    )

    # Benzersiz kullanici_adi (boş olanlar için sonra doldurulur)
    try:
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_kullanicilar_kadi ON Kullanicilar(kullanici_adi) WHERE kullanici_adi IS NOT NULL AND kullanici_adi != ''"
        )
    except Exception:
        pass

    conn.commit()
    logger.info("migrate_v2 tamamlandı")


def migrate_v3(conn) -> None:
    """Ekip davetleri, katılım istekleri, sosyal gönderiler, bildirim meta."""
    cur = conn.cursor()

    if not _kolon_var_mi(cur, "Ekipler", "herkese_acik"):
        cur.execute("ALTER TABLE Ekipler ADD COLUMN herkese_acik INTEGER NOT NULL DEFAULT 1")

    for kolon, tip in (
        ("ilgili_kullanici_id", "INTEGER"),
        ("ilgili_kayit_id", "INTEGER"),
    ):
        if not _kolon_var_mi(cur, "Bildirimler", kolon):
            cur.execute(f"ALTER TABLE Bildirimler ADD COLUMN {kolon} {tip}")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Ekip_Davetleri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ekip_id INTEGER NOT NULL,
            hedef_kullanici_id INTEGER NOT NULL,
            davet_eden_id INTEGER NOT NULL,
            rol_id INTEGER NOT NULL,
            durum TEXT NOT NULL DEFAULT 'beklemede',
            olusturma_tarihi TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (ekip_id) REFERENCES Ekipler(id) ON DELETE CASCADE,
            FOREIGN KEY (hedef_kullanici_id) REFERENCES Kullanicilar(id) ON DELETE CASCADE,
            FOREIGN KEY (davet_eden_id) REFERENCES Kullanicilar(id),
            FOREIGN KEY (rol_id) REFERENCES Roller(id)
        )
        """
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_davet_hedef ON Ekip_Davetleri(hedef_kullanici_id, durum)"
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Ekip_Katilim_Istekleri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ekip_id INTEGER NOT NULL,
            kullanici_id INTEGER NOT NULL,
            durum TEXT NOT NULL DEFAULT 'beklemede',
            mesaj TEXT DEFAULT '',
            olusturma_tarihi TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (ekip_id) REFERENCES Ekipler(id) ON DELETE CASCADE,
            FOREIGN KEY (kullanici_id) REFERENCES Kullanicilar(id) ON DELETE CASCADE
        )
        """
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_katilim_ekip ON Ekip_Katilim_Istekleri(ekip_id, durum)"
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Gonderiler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_id INTEGER NOT NULL,
            ekip_id INTEGER,
            icerik TEXT NOT NULL,
            olusturma_tarihi TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (kullanici_id) REFERENCES Kullanicilar(id) ON DELETE CASCADE,
            FOREIGN KEY (ekip_id) REFERENCES Ekipler(id) ON DELETE SET NULL
        )
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_gonderi_tarih ON Gonderiler(olusturma_tarihi DESC)")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Gonderi_Begeniler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gonderi_id INTEGER NOT NULL,
            kullanici_id INTEGER NOT NULL,
            tarih TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE (gonderi_id, kullanici_id),
            FOREIGN KEY (gonderi_id) REFERENCES Gonderiler(id) ON DELETE CASCADE,
            FOREIGN KEY (kullanici_id) REFERENCES Kullanicilar(id) ON DELETE CASCADE
        )
        """
    )

    conn.commit()
    logger.info("migrate_v3 tamamlandı")


def migrate_v4(conn) -> None:
    """Sosyal+, görev+, DM, sprint, duyuru, tercihler, yetenekler."""
    cur = conn.cursor()

    for tablo, kolon, tip in (
        ("Gonderiler", "gorunurluk", "TEXT NOT NULL DEFAULT 'herkes'"),
        ("Gorevler", "sprint_id", "INTEGER"),
        ("Kullanicilar", "son_gorulme", "TEXT"),
        ("Kullanicilar", "cevrimici", "INTEGER NOT NULL DEFAULT 0"),
    ):
        if not _kolon_var_mi(cur, tablo, kolon):
            cur.execute(f"ALTER TABLE {tablo} ADD COLUMN {kolon} {tip}")

    tablolar_sql = [
        """
        CREATE TABLE IF NOT EXISTS Gonderi_Kayitlari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gonderi_id INTEGER NOT NULL,
            kullanici_id INTEGER NOT NULL,
            tarih TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE (gonderi_id, kullanici_id),
            FOREIGN KEY (gonderi_id) REFERENCES Gonderiler(id) ON DELETE CASCADE,
            FOREIGN KEY (kullanici_id) REFERENCES Kullanicilar(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Sprintler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ekip_id INTEGER NOT NULL,
            ad TEXT NOT NULL,
            hedef TEXT DEFAULT '',
            baslangic TEXT,
            bitis TEXT,
            durum TEXT NOT NULL DEFAULT 'aktif',
            olusturma_tarihi TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (ekip_id) REFERENCES Ekipler(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Gorev_Sablonlari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ekip_id INTEGER NOT NULL,
            baslik TEXT NOT NULL,
            aciklama TEXT DEFAULT '',
            kritiklik TEXT NOT NULL DEFAULT 'Orta',
            olusturan_id INTEGER NOT NULL,
            olusturma_tarihi TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (ekip_id) REFERENCES Ekipler(id) ON DELETE CASCADE,
            FOREIGN KEY (olusturan_id) REFERENCES Kullanicilar(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Gorev_Ekleri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gorev_id INTEGER NOT NULL,
            dosya_yolu TEXT NOT NULL,
            dosya_adi TEXT NOT NULL,
            yukleyen_id INTEGER NOT NULL,
            tarih TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (gorev_id) REFERENCES Gorevler(id) ON DELETE CASCADE,
            FOREIGN KEY (yukleyen_id) REFERENCES Kullanicilar(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Gorev_Aktivite (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gorev_id INTEGER NOT NULL,
            kullanici_id INTEGER,
            ekip_id INTEGER,
            islem TEXT NOT NULL,
            detay TEXT,
            tarih TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (gorev_id) REFERENCES Gorevler(id) ON DELETE CASCADE,
            FOREIGN KEY (kullanici_id) REFERENCES Kullanicilar(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Ekip_Duyurulari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ekip_id INTEGER NOT NULL,
            yazar_id INTEGER NOT NULL,
            baslik TEXT NOT NULL,
            icerik TEXT NOT NULL,
            sabit INTEGER NOT NULL DEFAULT 0,
            olusturma_tarihi TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (ekip_id) REFERENCES Ekipler(id) ON DELETE CASCADE,
            FOREIGN KEY (yazar_id) REFERENCES Kullanicilar(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Bildirim_Tercihleri (
            kullanici_id INTEGER PRIMARY KEY,
            gorev_atama INTEGER NOT NULL DEFAULT 1,
            test_guncelleme INTEGER NOT NULL DEFAULT 1,
            scrum INTEGER NOT NULL DEFAULT 1,
            sosyal INTEGER NOT NULL DEFAULT 1,
            dm INTEGER NOT NULL DEFAULT 1,
            duyuru INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (kullanici_id) REFERENCES Kullanicilar(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Kullanici_Yetenekleri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_id INTEGER NOT NULL,
            etiket TEXT NOT NULL,
            UNIQUE (kullanici_id, etiket),
            FOREIGN KEY (kullanici_id) REFERENCES Kullanicilar(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Sohbetler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            olusturma_tarihi TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Sohbet_Uyeleri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sohbet_id INTEGER NOT NULL,
            kullanici_id INTEGER NOT NULL,
            UNIQUE (sohbet_id, kullanici_id),
            FOREIGN KEY (sohbet_id) REFERENCES Sohbetler(id) ON DELETE CASCADE,
            FOREIGN KEY (kullanici_id) REFERENCES Kullanicilar(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Mesajlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sohbet_id INTEGER NOT NULL,
            gonderen_id INTEGER NOT NULL,
            icerik TEXT NOT NULL,
            okundu INTEGER NOT NULL DEFAULT 0,
            tarih TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (sohbet_id) REFERENCES Sohbetler(id) ON DELETE CASCADE,
            FOREIGN KEY (gonderen_id) REFERENCES Kullanicilar(id)
        )
        """,
    ]
    for sql in tablolar_sql:
        cur.execute(sql)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_gorev_aktivite ON Gorev_Aktivite(gorev_id, tarih DESC)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_mesaj_sohbet ON Mesajlar(sohbet_id, tarih DESC)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sprint_ekip ON Sprintler(ekip_id)")

    conn.commit()
    logger.info("migrate_v4 tamamlandı")
