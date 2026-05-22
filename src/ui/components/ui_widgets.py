# -*- coding: utf-8 -*-
"""ui_widgets.py — Accordion, navbar buton, badge, drawer, yükleme."""

from __future__ import annotations

from typing import Any, Callable, Optional

import customtkinter as ctk

from src.ui.theme import (
    COLOR_BG_CARD,
    COLOR_BG_MUTED,
    COLOR_BORDER,
    COLOR_DANGER,
    COLOR_OVERLAY_SCRIM,
    COLOR_PRIMARY,
    COLOR_TEXT_MUTED,
    DRAWER_WIDTH,
    RADIUS_CARD,
    btn_ghost,
    font_baslik,
    font_govde,
    font_kucuk,
    surface_card,
)


class AccordionSection(ctk.CTkFrame):
    """Daraltılabilir bölüm (sol panel formlar için)."""

    def __init__(
        self,
        parent: Any,
        baslik: str,
        acik: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._acik = acik
        self._baslik_btn = ctk.CTkButton(
            self,
            text=("▼ " if acik else "▶ ") + baslik,
            anchor="w",
            fg_color=COLOR_BG_MUTED,
            hover_color=COLOR_BORDER,
            font=font_baslik(14),
            command=self._toggle,
        )
        self._baslik_btn.pack(fill="x", pady=(0, 4))
        self._icerik = ctk.CTkFrame(self, fg_color="transparent")
        if acik:
            self._icerik.pack(fill="x", pady=(0, 8))

    def _toggle(self) -> None:
        self._acik = not self._acik
        metin = self._baslik_btn.cget("text")
        if self._acik:
            self._baslik_btn.configure(text="▼ " + metin.lstrip("▶▼ ").lstrip())
            self._icerik.pack(fill="x", pady=(0, 8))
        else:
            self._baslik_btn.configure(text="▶ " + metin.lstrip("▶▼ ").lstrip())
            self._icerik.pack_forget()

    @property
    def body(self) -> ctk.CTkFrame:
        return self._icerik


class NavIconButton(ctk.CTkFrame):
    """Navbar ikon düğmesi + opsiyonel badge."""

    def __init__(
        self,
        parent: Any,
        ikon: str,
        tooltip: str = "",
        command: Optional[Callable[[], None]] = None,
        badge: int = 0,
        aktif: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._aktif = aktif
        fg = COLOR_BG_MUTED if aktif else "transparent"
        self._btn = ctk.CTkButton(
            self,
            text=ikon,
            width=44,
            height=40,
            fg_color=fg,
            hover_color=COLOR_BG_MUTED,
            font=ctk.CTkFont(size=18),
            command=command or (lambda: None),
        )
        self._btn.pack()
        if badge > 0:
            b = ctk.CTkFrame(self, width=20, height=18, corner_radius=9, fg_color=COLOR_DANGER)
            b.place(relx=0.85, rely=0.05, anchor="ne")
            b.pack_propagate(False)
            txt = "9+" if badge > 9 else str(badge)
            ctk.CTkLabel(b, text=txt, font=font_kucuk(9), text_color="white").pack(expand=True)
        if aktif:
            alt = ctk.CTkFrame(self, height=3, fg_color=COLOR_PRIMARY, corner_radius=2)
            alt.place(relx=0.5, rely=1.0, anchor="s", relwidth=0.7)

    def set_aktif(self, aktif: bool) -> None:
        self._aktif = aktif
        self._btn.configure(fg_color=COLOR_BG_MUTED if aktif else "transparent")


def drawer_overlay(
    master: ctk.CTkFrame,
    baslik: str,
    on_kapat: Callable[[], None],
) -> tuple[ctk.CTkFrame, ctk.CTkFrame]:
    """Standart çekmece: overlay + sağ panel."""
    overlay = ctk.CTkFrame(master, fg_color=COLOR_OVERLAY_SCRIM)
    overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

    panel = ctk.CTkFrame(overlay, width=DRAWER_WIDTH, fg_color=COLOR_BG_CARD, corner_radius=0, border_width=0)
    panel.pack(side="right", fill="y")
    panel.pack_propagate(False)

    ust = ctk.CTkFrame(panel, fg_color="transparent", height=52)
    ust.pack(fill="x", padx=16, pady=(12, 0))
    ust.pack_propagate(False)
    ctk.CTkLabel(ust, text=baslik, font=font_baslik(17)).pack(side="left", pady=10)
    btn_ghost(ust, "✕", width=40, height=36, command=on_kapat).pack(side="right", pady=8)

    ayir = ctk.CTkFrame(panel, height=1, fg_color=COLOR_BORDER)
    ayir.pack(fill="x", padx=16)

    icerik = ctk.CTkFrame(panel, fg_color="transparent")
    icerik.pack(fill="both", expand=True, padx=12, pady=12)
    return overlay, icerik


def yukleniyor_etiket(parent: Any, metin: str = "Yükleniyor…") -> ctk.CTkLabel:
    return ctk.CTkLabel(parent, text=metin, text_color=COLOR_TEXT_MUTED, font=font_govde())


def saglik_cubugu(parent: Any, skor: int, genislik: int = 280) -> ctk.CTkFrame:
    wrap = ctk.CTkFrame(parent, fg_color="transparent")
    wrap.pack(fill="x", pady=8)
    arka = ctk.CTkFrame(wrap, width=genislik, height=10, corner_radius=5, fg_color=COLOR_BG_MUTED)
    arka.pack(anchor="w")
    arka.pack_propagate(False)
    renk = "#2ecc71" if skor >= 70 else "#f39c12" if skor >= 40 else COLOR_DANGER
    dolu = max(4, int(genislik * skor / 100))
    ctk.CTkFrame(arka, width=dolu, height=10, corner_radius=5, fg_color=renk).place(x=0, y=0)
    return wrap
