# -*- coding: utf-8 -*-
"""theme.py — Tasarım sistemi: renkler, tipografi, yardımcılar."""

from __future__ import annotations

from typing import Any, Literal, Optional

import customtkinter as ctk

import src.config as config

# --- Marka ---
COLOR_PRIMARY = "#0A66C2"
COLOR_PRIMARY_HOVER = "#004182"
COLOR_ACCENT = "#5CE1E6"

# --- Yüzeyler (light, dark) ---
COLOR_BG_APP = ("#F3F2EF", "#1B1F23")
COLOR_BG_CARD = ("#FFFFFF", "#24292E")
COLOR_BG_ELEVATED = ("#FFFFFF", "#2D333B")
COLOR_BG_INPUT = ("#FAFAF9", "#1C2128")
COLOR_BG_MUTED = ("#F0EFEC", "#2A3038")
COLOR_BORDER = ("#E0DFDC", "#373E47")
COLOR_BORDER_FOCUS = ("#0A66C2", "#58A6FF")

COLOR_TEXT = ("#191919", "#E6EDF3")
COLOR_TEXT_MUTED = ("#5C5C5C", "#9BA3AF")
COLOR_COVER = ("#A0B4C8", "#2F4A63")

COLOR_SUCCESS = "#057642"
COLOR_WARNING = "#B24020"
COLOR_DANGER = "#CC1016"

# Çekmece / modal arka planı (Tkinter 8 haneli alpha desteklemez — düz renk)
COLOR_OVERLAY_SCRIM = ("#D8D8D4", "#12151A")

# --- Toast şerit (sol accent) ---
TOAST_STRIPE = {
    "success": COLOR_SUCCESS,
    "warning": COLOR_WARNING,
    "error": COLOR_DANGER,
    "info": COLOR_PRIMARY,
}

FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 26, "bold")
FONT_HEADING = (FONT_FAMILY, 18, "bold")
FONT_SUBHEAD = (FONT_FAMILY, 14, "bold")
FONT_BODY = (FONT_FAMILY, 13)
FONT_SMALL = (FONT_FAMILY, 11)
FONT_CAPTION = (FONT_FAMILY, 10)

RADIUS_CARD = 12
RADIUS_BUTTON = 8
AVATAR_SM = 36
AVATAR_MD = 96
AVATAR_LG = 152
DRAWER_WIDTH = 400
TOAST_WIDTH = 360
TOAST_GAP = 10
NAVBAR_HEIGHT = 56

# Kanban sütun şerit renkleri
DURUM_KOLON_RENK: dict[str, str] = {
    config.DURUM_BEKLEMEDE: "#6B7280",
    config.DURUM_KODLANIYOR: COLOR_PRIMARY,
    config.DURUM_KOD_INCELEMEDE: "#7C3AED",
    config.DURUM_TESTTE: "#D97706",
    config.DURUM_REVIZYON: COLOR_DANGER,
    config.DURUM_TAMAMLANDI: COLOR_SUCCESS,
}


def font_baslik(boyut: int = 18) -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=boyut, weight="bold")


def font_govde(boyut: int = 13) -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=boyut)


def font_kucuk(boyut: int = 11) -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=boyut)


def surface_card(
    parent: Any,
    elevated: bool = False,
    **kwargs: Any,
) -> ctk.CTkFrame:
    fg = COLOR_BG_ELEVATED if elevated else COLOR_BG_CARD
    return ctk.CTkFrame(
        parent,
        fg_color=fg,
        corner_radius=RADIUS_CARD,
        border_width=1,
        border_color=COLOR_BORDER,
        **kwargs,
    )


def btn_primary(parent: Any, text: str, command: Any = None, **kwargs: Any) -> ctk.CTkButton:
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        fg_color=COLOR_PRIMARY,
        hover_color=COLOR_PRIMARY_HOVER,
        corner_radius=RADIUS_BUTTON,
        font=font_govde(),
        **kwargs,
    )


def btn_secondary(parent: Any, text: str, command: Any = None, **kwargs: Any) -> ctk.CTkButton:
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        fg_color="transparent",
        border_width=1,
        border_color=COLOR_BORDER,
        text_color=COLOR_PRIMARY,
        hover_color=COLOR_BG_MUTED,
        corner_radius=RADIUS_BUTTON,
        font=font_govde(),
        **kwargs,
    )


def btn_ghost(parent: Any, text: str, command: Any = None, **kwargs: Any) -> ctk.CTkButton:
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        fg_color="transparent",
        hover_color=COLOR_BG_MUTED,
        text_color=COLOR_TEXT,
        corner_radius=RADIUS_BUTTON,
        font=font_govde(),
        **kwargs,
    )


def label_field(parent: Any, text: str) -> ctk.CTkLabel:
    return ctk.CTkLabel(parent, text=text, font=font_govde(13), anchor="w", text_color=COLOR_TEXT)


def entry_field(parent: Any, placeholder: str = "", **kwargs: Any) -> ctk.CTkEntry:
    return ctk.CTkEntry(
        parent,
        placeholder_text=placeholder,
        height=40,
        corner_radius=RADIUS_BUTTON,
        border_color=COLOR_BORDER,
        fg_color=COLOR_BG_INPUT,
        font=font_govde(),
        **kwargs,
    )


def online_dot(parent: Any, cevrimici: bool = False) -> ctk.CTkFrame:
    renk = COLOR_ACCENT if cevrimici else COLOR_TEXT_MUTED
    d = ctk.CTkFrame(parent, width=10, height=10, corner_radius=5, fg_color=renk)
    d.pack_propagate(False)
    return d


NavSayfa = Literal["ana", "profil", "ekip", "bildirim", "mesaj"]
