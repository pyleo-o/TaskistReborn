# -*- coding: utf-8 -*-
"""
services — İş kuralları ve UI ile veri katmanı arasındaki orkestrasyon.

Repository'leri doğrudan UI'a sızdırmadan, tek giriş noktaları sunar.
"""

from __future__ import annotations

from src.services.admin_task_service import AdminTaskService
from src.services.auth_service import AuthService
from src.services.dashboard_service import DashboardService
from src.services.developer_task_service import DeveloperTaskService
from src.services.tester_task_service import TesterTaskService
from src.services.workspace_service import WorkspaceService

__all__ = [
    "AuthService",
    "WorkspaceService",
    "DashboardService",
    "AdminTaskService",
    "DeveloperTaskService",
    "TesterTaskService",
]
