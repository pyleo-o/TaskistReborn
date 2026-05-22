# -*- coding: utf-8 -*-
"""
connection.py — SQLite bağlantı fabrikası.

CustomTkinter ana thread'inde çalışacağımız için çoğunlukla tek iş parçacığı
yeterlidir. Yine de sqlite3 bağlantısında check_same_thread=False kullanıyoruz;
böylece ileride arka plan iş parçacığına taşınırsa bağlantı anında kırılmaz.

Önemli: Her istek için uzun ömürlü tek bağlantı yerine, kısa ömürlü bağlantı
açıp kapatmak (with get_connection() as conn) veri bütünlüğü ve kilit sorunları
açısından daha güvenlidir.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional

import src.config as config


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Kısa ömürlü veritabanı bağlantısı bağlam yöneticisi (context manager).

    Kullanım:
        with get_connection() as conn:
            conn.execute("SELECT 1")

    Bağlantı blok sonunda otomatik kapatılır (commit/rollback çağıran kod
    sorumludur; bu fonksiyon sadece close garantisi verir).
    """
    conn: Optional[sqlite3.Connection] = None
    try:
        # timeout: başka işlem kilitliyse kısa süre bekle (masaüstü demo için yeterli)
        conn = sqlite3.connect(
            config.VERITABANI_YOLU,
            timeout=15.0,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                # Bağlantı zaten kapalıysa veya disk hatası varsa: uygulama çökmesin.
                pass
