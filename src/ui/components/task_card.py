# -*- coding: utf-8 -*-
"""task_card.py — Jira/Trello tarzı görev kartı."""

from __future__ import annotations

from typing import Any, Callable, Optional

import customtkinter as ctk

import src.config as config
from src.ui.theme import (
    COLOR_BG_CARD,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_TEXT_MUTED,
    btn_secondary,
    font_baslik,
    font_kucuk,
)
from src.ui.ui_utils import due_date_gecikmis_mi, kart_kenarligi


def modern_gorev_karti(
    parent: Any,
    g: dict[str, Any],
    on_sec: Optional[Callable[[dict[str, Any]], None]] = None,
    on_detay: Optional[Callable[[dict[str, Any]], None]] = None,
    compact: bool = False,
    secili: bool = False,
) -> ctk.CTkFrame:
    kid = int(g["id"])
    kritiklik = str(g.get("kritiklik") or "")
    durum = str(g.get("durum") or "")
    bw, bc = kart_kenarligi(kritiklik, durum, g.get("due_date"), g.get("revize_kritikligi"))
    if secili:
        bw = 2
        bc = COLOR_PRIMARY
    gecikme = due_date_gecikmis_mi(g.get("due_date"))

    kart = ctk.CTkFrame(
        parent,
        fg_color=COLOR_BG_CARD,
        corner_radius=10,
        border_width=bw,
        border_color=bc,
        cursor="hand2",
    )
    kart.pack(fill="x", padx=4, pady=5)

    if on_sec:
        gg = dict(g)

        def _tikla(_e: Any = None, data: dict[str, Any] = gg) -> None:
            on_sec(data)

        kart.bind("<Button-1>", _tikla)
        for child in (kart,):
            pass

    ust = ctk.CTkFrame(kart, fg_color="transparent")
    ust.pack(fill="x", padx=12, pady=(10, 4))
    chip_renk = COLOR_DANGER if kritiklik == config.ONCELIK_KRITIK else COLOR_PRIMARY
    ctk.CTkLabel(
        ust,
        text=kritiklik[:12],
        font=font_kucuk(10),
        fg_color=chip_renk,
        corner_radius=6,
        text_color="white",
        width=56,
        height=22,
    ).pack(side="left")
    ctk.CTkLabel(ust, text=f"#{kid}", text_color=COLOR_TEXT_MUTED, font=font_kucuk()).pack(side="right")

    baslik = str(g.get("baslik") or "")
    if gecikme:
        baslik += "  · GECİKMİŞ"
    lbl = ctk.CTkLabel(
        kart,
        text=baslik,
        font=font_baslik(13 if compact else 14),
        wraplength=260 if compact else 400,
        justify="left",
    )
    lbl.pack(anchor="w", padx=12, pady=(0, 4))
    if on_sec:
        lbl.bind("<Button-1>", lambda e, data=dict(g): on_sec(data))

    meta = f"{durum}"
    if g.get("atanan_gosterim"):
        meta += f"  ·  {g.get('atanan_gosterim')}"
    if g.get("due_date"):
        meta += f"  ·  {g.get('due_date')}"
    ctk.CTkLabel(kart, text=meta, text_color=COLOR_TEXT_MUTED, font=font_kucuk()).pack(
        anchor="w", padx=12, pady=(0, 8)
    )

    btn_row = ctk.CTkFrame(kart, fg_color="transparent")
    btn_row.pack(fill="x", padx=10, pady=(0, 10))
    if on_detay:
        btn_secondary(btn_row, "Detay", width=64, height=28, command=lambda: on_detay(dict(g))).pack(
            side="left", padx=2
        )
    return kart
