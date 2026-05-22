# -*- coding: utf-8 -*-
"""
repositories — Veritabanı erişim katmanı (saf SQL / satır eşleme).

Servisler iş kuralını burada tutmaz; yalnızca sorgu ve veri taşıma yapılır.
"""

from __future__ import annotations

from src.repositories.tasks_repository import TasksRepository
from src.repositories.teams_repository import TeamsRepository
from src.repositories.users_repository import UsersRepository

__all__ = ["UsersRepository", "TeamsRepository", "TasksRepository"]
