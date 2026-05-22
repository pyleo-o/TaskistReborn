# -*- coding: utf-8 -*-
"""toast.py — Sağ üstte kayan toast (ayrı pencere yok, modal yok)."""

from __future__ import annotations

from typing import Literal, Optional

import customtkinter as ctk

from src.ui.theme import (
    COLOR_BG_CARD,
    COLOR_TEXT,
    TOAST_GAP,
    TOAST_STRIPE,
    TOAST_WIDTH,
    font_baslik,
    font_govde,
)

ToastTip = Literal["success", "warning", "error", "info"]

_STIL: dict[ToastTip, dict[str, str]] = {
    "success": {"stripe": TOAST_STRIPE["success"], "ikon": "✓"},
    "warning": {"stripe": TOAST_STRIPE["warning"], "ikon": "!"},
    "error": {"stripe": TOAST_STRIPE["error"], "ikon": "✕"},
    "info": {"stripe": TOAST_STRIPE["info"], "ikon": "i"},
}


class ToastManager:
    """Her toast ayrı borderless mini pencere; sağ üstte hizalanır."""

    def __init__(self, root: ctk.CTk, varsayilan_sure_ms: int = 4500) -> None:
        self._root = root
        self._sure = varsayilan_sure_ms
        self._aktif: list[ctk.CTkToplevel] = []
        self._offset_y = 64

    def goster(
        self,
        mesaj: str,
        tip: ToastTip = "info",
        baslik: Optional[str] = None,
        sure_ms: Optional[int] = None,
    ) -> None:
        if not (mesaj or "").strip():
            return

        st = _STIL.get(tip, _STIL["info"])
        baslik_metin = baslik or {
            "success": "Başarılı",
            "warning": "Uyarı",
            "error": "Hata",
            "info": "Bilgi",
        }[tip]

        win = ctk.CTkToplevel(self._root)
        win.wm_overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(fg_color=COLOR_BG_CARD)

        frm = ctk.CTkFrame(win, fg_color=COLOR_BG_CARD, corner_radius=10, border_width=1, border_color=st["stripe"])
        frm.pack(fill="both", expand=True, padx=1, pady=1)

        govde = ctk.CTkFrame(frm, fg_color="transparent")
        govde.pack(fill="both", expand=True)

        serit = ctk.CTkFrame(govde, width=4, fg_color=st["stripe"], corner_radius=2)
        serit.pack(side="left", fill="y", padx=(0, 0), pady=0)

        sag = ctk.CTkFrame(govde, fg_color="transparent")
        sag.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        baslik_satir = ctk.CTkFrame(sag, fg_color="transparent")
        baslik_satir.pack(fill="x")

        ctk.CTkLabel(
            baslik_satir,
            text=f"{st['ikon']}  {baslik_metin}",
            font=font_baslik(13),
            text_color=COLOR_TEXT,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            baslik_satir,
            text="✕",
            width=28,
            height=28,
            fg_color="transparent",
            command=lambda w=win: self._kapat(w),
        ).pack(side="right")

        ctk.CTkLabel(
            sag,
            text=mesaj.strip(),
            wraplength=TOAST_WIDTH - 40,
            justify="left",
            font=font_govde(12),
            text_color=COLOR_TEXT,
        ).pack(anchor="w", pady=(4, 4))

        win.update_idletasks()
        w = TOAST_WIDTH
        h = win.winfo_reqheight()
        rx = self._root.winfo_rootx()
        ry = self._root.winfo_rooty()
        rw = self._root.winfo_width()
        x = rx + rw - w - 20
        y = ry + self._offset_y + len(self._aktif) * (h + TOAST_GAP)
        win.geometry(f"{w}x{h}+{x}+{y}")

        self._aktif.append(win)
        sure = sure_ms if sure_ms is not None else self._sure
        self._root.after(sure, lambda w=win: self._kapat(w))

    def _kapat(self, win: ctk.CTkToplevel) -> None:
        if win in self._aktif:
            self._aktif.remove(win)
        try:
            win.destroy()
        except Exception:
            pass
        self._yeniden_konumla()

    def _yeniden_konumla(self) -> None:
        rx = self._root.winfo_rootx()
        ry = self._root.winfo_rooty()
        rw = self._root.winfo_width()
        y = ry + self._offset_y
        for win in self._aktif:
            try:
                win.update_idletasks()
                w = TOAST_WIDTH
                h = win.winfo_height()
                x = rx + rw - w - 20
                win.geometry(f"{w}x{h}+{x}+{y}")
                y += h + TOAST_GAP
            except Exception:
                pass

    def temizle(self) -> None:
        for w in list(self._aktif):
            self._kapat(w)
