# -*- coding: utf-8 -*-
"""
db paketi — SQLite bağlantısı ve şema başlatma.

Dışarıdan tipik kullanım:
    from src.db import get_connection, init_database

init_database(): Uygulama ilk açılışında çağrılır; tablolar yoksa oluşturur,
yalnızca temel rolleri (5 rol) seed eder; kullanıcı/ekip demo verisi eklemez.
"""

from __future__ import annotations

from src.db.connection import get_connection
from src.db.schema import init_database

__all__ = ["get_connection", "init_database"]
