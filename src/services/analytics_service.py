# -*- coding: utf-8 -*-
"""analytics_service.py — Görev süre analizi raporu."""

from __future__ import annotations

from typing import Any

from src.repositories.tasks_repository import TasksRepository


class AnalyticsService:
    def __init__(self, ekip_id: int, repo: TasksRepository | None = None) -> None:
        self._ekip_id = int(ekip_id)
        self._repo = repo or TasksRepository()

    def performans_raporu(self) -> dict[str, Any]:
        satirlar = self._repo.ekip_tamamlanan_sure_raporu(self._ekip_id)
        sureler = [int(r.get("sure_saniye") or 0) for r in satirlar if r.get("sure_saniye") is not None]
        ort = int(sum(sureler) / len(sureler)) if sureler else 0
        return {
            "satirlar": satirlar,
            "ortalama_saniye": ort,
            "tamamlanan_adet": len(sureler),
        }
