# -*- coding: utf-8 -*-
"""tooltip.py — Kapatılabilir bilgi kutusu (✕ ile)."""

from __future__ import annotations

from typing import Any, Optional

import customtkinter as ctk

from src.ui.theme import COLOR_BG_CARD, COLOR_BORDER, COLOR_TEXT_MUTED

_aktif: Optional["CTkTooltip"] = None


class CTkTooltip:
    """Fare üzerine gelince açıklama; ✕ veya fare ayrılınca kapanır."""

    def __init__(self, widget: Any, text: str, gecikme_ms: int = 500) -> None:
        self._widget = widget
        self._text = text
        self._gecikme = gecikme_ms
        self._tip: Optional[ctk.CTkToplevel] = None
        self._after_id: Optional[str] = None

        widget.bind("<Enter>", self._enter, add="+")
        widget.bind("<Leave>", self._leave, add="+")
        widget.bind("<ButtonPress>", self._gizle, add="+")

    def _enter(self, _event: Any = None) -> None:
        self._iptal()
        self._after_id = self._widget.after(self._gecikme, self._goster)

    def _leave(self, _event: Any = None) -> None:
        self._iptal()
        if self._tip is None:
            return
        self._after_id = self._widget.after(250, self._leave_kontrol)

    def _leave_kontrol(self) -> None:
        self._after_id = None
        if self._tip is None:
            return
        try:
            x, y = self._widget.winfo_pointerxy()
            tx, ty = self._tip.winfo_rootx(), self._tip.winfo_rooty()
            tw, th = self._tip.winfo_width(), self._tip.winfo_height()
            if tx <= x <= tx + tw and ty <= y <= ty + th:
                return
            wx, wy = self._widget.winfo_rootx(), self._widget.winfo_rooty()
            ww, wh = self._widget.winfo_width(), self._widget.winfo_height()
            if wx <= x <= wx + ww and wy <= y <= wy + wh:
                return
        except Exception:
            pass
        self._gizle()

    def _iptal(self) -> None:
        if self._after_id is not None:
            try:
                self._widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _goster(self) -> None:
        global _aktif
        if self._tip is not None:
            return
        if _aktif is not None and _aktif is not self:
            _aktif._gizle()

        try:
            x = self._widget.winfo_rootx() + 8
            y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        except Exception:
            return

        self._tip = ctk.CTkToplevel(self._widget)
        self._tip.wm_overrideredirect(True)
        self._tip.attributes("-topmost", True)
        self._tip.geometry(f"+{x}+{y}")

        kutu = ctk.CTkFrame(
            self._tip,
            fg_color=COLOR_BG_CARD,
            corner_radius=8,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        kutu.pack()

        ust = ctk.CTkFrame(kutu, fg_color="transparent")
        ust.pack(fill="x", padx=6, pady=(6, 0))

        ctk.CTkLabel(
            ust,
            text=self._text,
            wraplength=260,
            justify="left",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MUTED,
        ).pack(side="left", padx=(6, 4), pady=4)

        ctk.CTkButton(
            ust,
            text="✕",
            width=26,
            height=26,
            fg_color="transparent",
            hover_color=("gray80", "gray30"),
            text_color=COLOR_TEXT_MUTED,
            command=self._gizle,
        ).pack(side="right", padx=2)

        self._tip.bind("<Leave>", lambda _e: self._gizle())
        _aktif = self

    def _gizle(self) -> None:
        global _aktif
        self._iptal()
        if self._tip is not None:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None
        if _aktif is self:
            _aktif = None


def tooltip_kapat_hepsi() -> None:
    """Açık tüm ipuçlarını kapat (sayfa değişiminde)."""
    global _aktif
    if _aktif is not None:
        _aktif._gizle()


def tooltip_ekle(widget: Any, anahtar: str) -> None:
    """config.UI_TOOLTIP_METINLERI anahtarından metin bağlar."""
    import src.config as config

    metin = config.UI_TOOLTIP_METINLERI.get(anahtar)
    if metin:
        CTkTooltip(widget, metin)
