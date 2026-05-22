# -*- coding: utf-8 -*-
"""empty_state.py — Boş durum kartı + isteğe bağlı CTA."""

from __future__ import annotations

from typing import Any, Callable, Optional

import customtkinter as ctk

from src.ui.theme import COLOR_TEXT_MUTED, btn_primary, font_baslik, font_govde, surface_card


def bos_durum_karti(
    parent: ctk.CTkFrame,
    emoji: str = "📭",
    baslik: str = "Henüz içerik yok",
    aciklama: str = "",
    cta_metin: Optional[str] = None,
    cta_command: Optional[Callable[[], None]] = None,
) -> ctk.CTkFrame:
    kart = surface_card(parent)
    kart.pack(fill="x", padx=4, pady=8)
    ctk.CTkLabel(kart, text=emoji, font=ctk.CTkFont(size=42)).pack(pady=(20, 4))
    ctk.CTkLabel(kart, text=baslik, font=font_baslik(14)).pack(pady=4)
    if aciklama:
        ctk.CTkLabel(
            kart,
            text=aciklama,
            text_color=COLOR_TEXT_MUTED,
            wraplength=360,
            justify="center",
            font=font_govde(12),
        ).pack(padx=20, pady=(0, 12))
    if cta_metin and cta_command:
        btn_primary(kart, cta_metin, command=cta_command, height=36).pack(pady=(0, 20), padx=40, fill="x")
    else:
        ctk.CTkLabel(kart, text="").pack(pady=8)
    return kart
