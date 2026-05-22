# -*- coding: utf-8 -*-
"""
schema.py — SQLite tablolarının oluşturulması ve yalnızca rol sözlüğü seed'i.

Mimari özeti (sizin onayladığınız çoklu çalışma alanı modeli):
- Kullanicilar: global kimlik; rol YOKTUR.
- Ekipler: çalışma alanı (workspace).
- Ekip_Uyeleri: kullanıcı ↔ ekip çoktan çoğa ilişki; rol_id BU tabloda tutulur.
- Gorevler: görevler ekibe bağlıdır; due_date ile süre takibi UI'da kırmızı vurgu için kullanılır.
- AltGorevler: ana göreve bağlı onay kutulu alt işler.
- ScrumGunluk: günlük scrum cevapları (ekip + kullanıcı + tarih tekil).
- Islem_Loglari: atama–tamamlanma süreleri vb. denetim izi.
- Bildirimler: e-posta yerine uygulama içi bildirim kuyruğu (simülasyon).

Tüm kritik adımlar try/except ile korunur; hata mesajları üst katmana
Exception metni ile iletilir (UI MessageBox orada gösterilecek).
"""

from __future__ import annotations

import logging

import src.config as config
from src.db.connection import get_connection
from src.db.migrations import migrate_v2, migrate_v3, migrate_v4

logger = logging.getLogger(__name__)


def _create_tables(conn) -> None:
    """CREATE IF NOT EXISTS ifadeleri — mevcut kuruluma zarar vermez."""
    cur = conn.cursor()
    # Foreign key kısıtlarının uygulanması için önce açılmalı (SQLite gereksinimi).
    cur.execute("PRAGMA foreign_keys = ON")

    # --- Roller: sistemde tanımlı sabit rol sözlüğü ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Roller (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rol_adi TEXT NOT NULL UNIQUE
        )
        """
    )

    # --- Kullanicilar: ortak giriş (e-posta + şifre); GLOBAL ROL YOK ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Kullanicilar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            sifre TEXT NOT NULL,
            ad_soyad TEXT NOT NULL DEFAULT '',
            olusturma_tarihi TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )

    # --- Ekipler (Workspace): proje/ekip çalışma alanı ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Ekipler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            aciklama TEXT DEFAULT '',
            olusturan_kullanici_id INTEGER NOT NULL,
            olusturma_tarihi TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (olusturan_kullanici_id) REFERENCES Kullanicilar(id)
        )
        """
    )

    # --- Ekip_Uyeleri: many-to-many + ekip bazlı rol ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Ekip_Uyeleri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ekip_id INTEGER NOT NULL,
            kullanici_id INTEGER NOT NULL,
            rol_id INTEGER NOT NULL,
            katilim_tarihi TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE (ekip_id, kullanici_id),
            FOREIGN KEY (ekip_id) REFERENCES Ekipler(id) ON DELETE CASCADE,
            FOREIGN KEY (kullanici_id) REFERENCES Kullanicilar(id) ON DELETE CASCADE,
            FOREIGN KEY (rol_id) REFERENCES Roller(id)
        )
        """
    )

    # --- Gorevler: ekibe bağlı kartlar ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Gorevler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ekip_id INTEGER NOT NULL,
            baslik TEXT NOT NULL,
            aciklama TEXT DEFAULT '',
            kritiklik TEXT NOT NULL,
            durum TEXT NOT NULL,
            olusturan_kullanici_id INTEGER NOT NULL,
            atanan_kullanici_id INTEGER,
            due_date TEXT,
            revize_kritikligi TEXT,
            kod_metni TEXT,
            son_tarama_ozeti TEXT,
            atama_zamani TEXT,
            tamamlanma_zamani TEXT,
            olusturma_tarihi TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (ekip_id) REFERENCES Ekipler(id) ON DELETE CASCADE,
            FOREIGN KEY (olusturan_kullanici_id) REFERENCES Kullanicilar(id),
            FOREIGN KEY (atanan_kullanici_id) REFERENCES Kullanicilar(id)
        )
        """
    )

    # --- AltGorevler: checkbox mantığı için tamamlandi bayrağı ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS AltGorevler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gorev_id INTEGER NOT NULL,
            baslik TEXT NOT NULL,
            tamamlandi INTEGER NOT NULL DEFAULT 0,
            sira INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (gorev_id) REFERENCES Gorevler(id) ON DELETE CASCADE
        )
        """
    )

    # --- ScrumGunluk: günlük üç soru; ekip bağlamı ile ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ScrumGunluk (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_id INTEGER NOT NULL,
            ekip_id INTEGER NOT NULL,
            tarih TEXT NOT NULL,
            dun_yaptiklarim TEXT DEFAULT '',
            bugun_yapacaklarim TEXT DEFAULT '',
            engel_var_mi TEXT DEFAULT '',
            UNIQUE (kullanici_id, ekip_id, tarih),
            FOREIGN KEY (kullanici_id) REFERENCES Kullanicilar(id) ON DELETE CASCADE,
            FOREIGN KEY (ekip_id) REFERENCES Ekipler(id) ON DELETE CASCADE
        )
        """
    )

    # --- Islem_Loglari: süre ve önemli işlemler ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Islem_Loglari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_id INTEGER,
            ekip_id INTEGER,
            gorev_id INTEGER,
            islem_tipi TEXT NOT NULL,
            detay TEXT,
            tarih TEXT NOT NULL DEFAULT (datetime('now')),
            sure_saniye INTEGER,
            FOREIGN KEY (kullanici_id) REFERENCES Kullanicilar(id),
            FOREIGN KEY (ekip_id) REFERENCES Ekipler(id),
            FOREIGN KEY (gorev_id) REFERENCES Gorevler(id)
        )
        """
    )

    # --- Bildirimler: SMTP simülasyonu (uygulama içi) ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Bildirimler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_id INTEGER NOT NULL,
            ekip_id INTEGER,
            baslik TEXT NOT NULL,
            mesaj TEXT NOT NULL,
            okundu INTEGER NOT NULL DEFAULT 0,
            tip TEXT NOT NULL DEFAULT 'GENEL',
            olusturma_tarihi TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (kullanici_id) REFERENCES Kullanicilar(id) ON DELETE CASCADE,
            FOREIGN KEY (ekip_id) REFERENCES Ekipler(id) ON DELETE SET NULL
        )
        """
    )

    # Sorgu performansı için indeksler
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_ekip_uyeleri_kullanici ON Ekip_Uyeleri(kullanici_id)"
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ekip_uyeleri_ekip ON Ekip_Uyeleri(ekip_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_gorevler_ekip ON Gorevler(ekip_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_gorevler_atanan ON Gorevler(atanan_kullanici_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_altgorevler_gorev ON AltGorevler(gorev_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_bildirim_kullanici ON Bildirimler(kullanici_id)")


def _seed_roller(conn) -> dict[str, int]:
    """Roller tablosuna 5 rolü ekler; rol_adi -> id sözlüğü döner."""
    cur = conn.cursor()
    rol_idleri: dict[str, int] = {}
    for rol_adi in config.VARSAYILAN_ROLLER:
        try:
            cur.execute("INSERT OR IGNORE INTO Roller (rol_adi) VALUES (?)", (rol_adi,))
        except Exception as ex:
            logger.exception("Rol eklenemedi: %s", rol_adi)
            raise RuntimeError(f"Rol seed hatası ({rol_adi}): {ex}") from ex
    conn.commit()
    cur.execute("SELECT id, rol_adi FROM Roller")
    for row in cur.fetchall():
        rol_idleri[row["rol_adi"]] = int(row["id"])
    return rol_idleri


def _seed_demo(conn) -> None:
    """Sunum için örnek kullanıcı/ekip (TASKIST_SEED_DEMO=1)."""
    import os
    from src.utils.password_util import sifre_hashle

    if os.environ.get("TASKIST_SEED_DEMO", "").strip() not in ("1", "true", "yes"):
        return
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM Kullanicilar")
    if int(cur.fetchone()["c"]) > 0:
        return
    cur.execute(
        "INSERT INTO Kullanicilar (email, sifre, ad_soyad, kullanici_adi) VALUES (?,?,?,?)",
        ("yonetici@demo.com", sifre_hashle("demo"), "Demo Yönetici", "demo_yonetici"),
    )
    yid = int(cur.lastrowid)
    cur.execute(
        "INSERT INTO Ekipler (ad, aciklama, olusturan_kullanici_id) VALUES (?,?,?)",
        ("Demo Ekip", "Sunum workspace", yid),
    )
    eid = int(cur.lastrowid)
    cur.execute("SELECT id FROM Roller WHERE rol_adi = ? LIMIT 1", (config.ROL_YONETICI,))
    rid = int(cur.fetchone()["id"])
    cur.execute(
        "INSERT INTO Ekip_Uyeleri (ekip_id, kullanici_id, rol_id) VALUES (?,?,?)",
        (eid, yid, rid),
    )
    conn.commit()


def init_database() -> None:
    """
    Veritabanını başlatır: tabloları oluşturur ve yalnızca temel rolleri seed eder.

    Kullanıcı / ekip / görev demo verisi bilinçli olarak YOKTUR; sunumda sistem
    sıfırdan (Kayıt Ol + Yeni Ekip) anlatılır.

    Raises:
        Exception: Dosya izni, SQL sözdizimi vb. ciddi hatalarda (üst katman yakalar).
    """
    try:
        with get_connection() as conn:
            try:
                # SQLite foreign key desteği bağlantı bazlıdır; her bağlantıda açmak güvenlidir.
                conn.execute("PRAGMA foreign_keys = ON")
                _create_tables(conn)
                conn.commit()
                _seed_roller(conn)
                migrate_v2(conn)
                migrate_v3(conn)
                migrate_v4(conn)
                _seed_demo(conn)
            except Exception:
                conn.rollback()
                raise
    except Exception as ex:
        logger.exception("Veritabanı başlatılamadı")
        raise RuntimeError(f"init_database başarısız: {ex}") from ex
