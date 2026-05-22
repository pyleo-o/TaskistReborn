# -*- coding: utf-8 -*-
"""Veritabanı dosyasını siler ve şemayı yeniden oluşturur."""

from __future__ import annotations

import os
import sys

import src.config as config
from src.db.schema import init_database


def reset_database() -> None:
    yol = config.VERITABANI_YOLU
    if os.path.isfile(yol):
        try:
            os.remove(yol)
            print(f"Silindi: {yol}")
        except PermissionError:
            print(f"Kapatın: {yol} kullanımda, silinemedi.")
            sys.exit(1)
    init_database()
    print("Yeni veritabanı oluşturuldu (boş, yalnızca roller).")


if __name__ == "__main__":
    reset_database()
