# -*- coding: utf-8 -*-
"""
dashboard_service.py — Ekip içi role göre hangi dashboard'un yükleneceğini belirler.

Rapor / sunum sadeleştirmesi:
- 'Yönetici' → yönetici paneli
- 'Tester' → tester paneli
- Diğer tüm roller (Backend/Frontend/Sistem Analisti) → geliştirici paneli
"""

from __future__ import annotations

import src.config as config


class DashboardService:
    """Rol adı → ekran türü eşlemesi."""

    EKRAN_YONETICI = "admin"
    EKRAN_YAZILIMCI = "developer"
    EKRAN_TESTER = "tester"

    @staticmethod
    def ekran_turu_rolden(rol_adi: str) -> str:
        """
        Veritabanındaki rol_adi değerini UI router anahtarına çevirir.

        Args:
            rol_adi: Ekip_Uyeleri + Roller join sonucu gelen metin.

        Returns:
            'admin' | 'developer' | 'tester'
        """
        if rol_adi == config.ROL_YONETICI:
            return DashboardService.EKRAN_YONETICI
        if rol_adi == config.ROL_TESTER:
            return DashboardService.EKRAN_TESTER
        return DashboardService.EKRAN_YAZILIMCI

    @staticmethod
    def ekran_basligi(rol_adi: str, ekip_ad: str) -> str:
        """Pencere alt başlığı / iç başlık için kısa metin."""
        return f"{ekip_ad} — {rol_adi}"
