# -*- coding: utf-8 -*-
"""
dialogs.py — CustomTkinter uyumlu modal uyarı pencereleri.

Not: CustomTkinter 5.2.x paketinde CTkMessagebox bulunmadığı için,
koyu temaya uygun CTkToplevel tabanlı basit diyaloglar kullanıyoruz.
(Bu, sunumda 'şık pop-up' ve tutarlı görünüm gereksinimini karşılar.)
"""

from __future__ import annotations

from typing import Literal, Optional

import customtkinter as ctk

DialogTip = Literal["info", "warning", "error"]


def _kok_pencere(master: ctk.CTk | ctk.CTkFrame | ctk.CTkToplevel) -> ctk.CTk:
    """Frame içinden ana CTk kökünü bulur."""
    w = master
    while w is not None:
        if isinstance(w, ctk.CTk):
            return w
        w = getattr(w, "master", None)  # type: ignore[assignment]
    raise RuntimeError("CTk kök penceresi bulunamadı.")


def ctk_mesaj_goster(
    master: ctk.CTk | ctk.CTkFrame,
    baslik: str,
    mesaj: str,
    tip: DialogTip = "info",
) -> None:
    """
    Kullanıcıya modal mesaj gösterir (Tamam ile kapanır).

    Args:
        master: Genelde ana kabuk veya aktif frame (üst pencereye transient bağlanır).
        baslik: Pencere başlığı.
        mesaj: Uzun metinler için wraplength kullanılır.
        tip: info / warning / error — vurgu rengi için.
    """
    kok = _kok_pencere(master)

    renk = "#1f6aa5"
    if tip == "warning":
        renk = "#b8860b"
    elif tip == "error":
        renk = "#c0392b"

    win = ctk.CTkToplevel(kok)
    win.title(baslik)
    win.geometry("460x220")
    win.resizable(False, False)
    try:
        win.transient(kok)
    except Exception:
        pass
    win.grab_set()

    ust = ctk.CTkFrame(win, fg_color=renk, corner_radius=0)
    ust.pack(fill="x")
    ctk.CTkLabel(ust, text=baslik, font=ctk.CTkFont(size=16, weight="bold"), text_color="white").pack(
        padx=16, pady=12, anchor="w"
    )

    govde = ctk.CTkFrame(win, fg_color="transparent")
    govde.pack(fill="both", expand=True, padx=16, pady=12)

    ctk.CTkLabel(
        govde,
        text=mesaj,
        wraplength=420,
        justify="left",
        font=ctk.CTkFont(size=14),
    ).pack(fill="both", expand=True, anchor="nw")

    def _kapat() -> None:
        try:
            win.grab_release()
        except Exception:
            pass
        win.destroy()

    btn = ctk.CTkButton(win, text="Tamam", width=140, command=_kapat)
    btn.pack(pady=(0, 14))

    win.protocol("WM_DELETE_WINDOW", _kapat)
    try:
        win.after(50, win.focus_force)
    except Exception:
        pass


def ctk_bilgi(master: ctk.CTk | ctk.CTkFrame, baslik: str, mesaj: str) -> None:
    """Kısayol: bilgi tipi."""
    ctk_mesaj_goster(master, baslik, mesaj, tip="info")


def ctk_uyari(master: ctk.CTk | ctk.CTkFrame, baslik: str, mesaj: str) -> None:
    """Kısayol: uyarı tipi."""
    ctk_mesaj_goster(master, baslik, mesaj, tip="warning")


def ctk_hata(master: ctk.CTk | ctk.CTkFrame, baslik: str, mesaj: str) -> None:
    """Kısayol: hata tipi."""
    ctk_mesaj_goster(master, baslik, mesaj, tip="error")
