# -*- coding: utf-8 -*-
"""analytics_service.py — Görev süre analizi ve ekip performans takibi."""

from __future__ import annotations

from typing import Any

from src.repositories.tasks_repository import TasksRepository


def sure_metni(saniye: int) -> str:
    """Saniyeyi rapor/sunum için okunabilir metne çevirir."""
    s = max(0, int(saniye))
    if s < 60:
        return f"{s} sn"
    dk = s // 60
    if dk < 60:
        return f"{dk} dk ({s} sn)"
    sa = dk // 60
    kalan_dk = dk % 60
    return f"{sa} sa {kalan_dk} dk"


class AnalyticsService:
    def __init__(self, ekip_id: int, repo: TasksRepository | None = None) -> None:
        self._ekip_id = int(ekip_id)
        self._repo = repo or TasksRepository()

    def performans_raporu(self) -> dict[str, Any]:
        satirlar = self._repo.ekip_tamamlanan_sure_raporu(self._ekip_id)
        sureler = [int(r.get("sure_saniye") or 0) for r in satirlar if r.get("sure_saniye") is not None]
        ort = int(sum(sureler) / len(sureler)) if sureler else 0
        toplam = int(sum(sureler))

        uye_ozetleri = self._repo.ekip_uye_performans_ozeti(self._ekip_id)
        for u in uye_ozetleri:
            uid = int(u.get("kullanici_id") or 0)
            if uid:
                u["aktif_gorev"] = self._repo.atanan_aktif_gorev_sayisi_ekipte(self._ekip_id, uid)
            else:
                u["aktif_gorev"] = 0
            u["ortalama_metin"] = sure_metni(int(u.get("ortalama_saniye") or 0))
            u["toplam_metin"] = sure_metni(int(u.get("toplam_saniye") or 0))

        return {
            "satirlar": satirlar,
            "ortalama_saniye": ort,
            "ortalama_metin": sure_metni(ort),
            "toplam_saniye": toplam,
            "toplam_metin": sure_metni(toplam),
            "tamamlanan_adet": len(sureler),
            "uye_ozetleri": uye_ozetleri,
        }
