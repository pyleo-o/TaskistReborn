# -*- coding: utf-8 -*-
"""
main.py — Taskist Reborn masaüstü uygulaması giriş noktası.

Çalıştırma (TaskistReborn klasöründe):
    python main.py
"""

from __future__ import annotations

import os
import sys

# Proje kökünü import yoluna ekle (src paketi)
_PROJE_KOKU = os.path.dirname(os.path.abspath(__file__))
if _PROJE_KOKU not in sys.path:
    sys.path.insert(0, _PROJE_KOKU)


def main() -> None:
    from src.ui.app_shell import AppShell

    app = AppShell()
    app.calistir()


if __name__ == "__main__":
    main()
