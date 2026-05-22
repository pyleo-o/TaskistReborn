# -*- coding: utf-8 -*-
"""notifications_panel.py — Etkileşimli bildirim çekmecesi."""

from __future__ import annotations

from typing import Any, Callable, Optional

import customtkinter as ctk

import src.config as config
from src.services.notification_service import NotificationService
from src.services.social_service import SocialService
from src.ui.theme import COLOR_BG_CARD, COLOR_BORDER, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_TEXT_MUTED, DRAWER_WIDTH


class NotificationsDrawer(ctk.CTkFrame):
    def __init__(
        self,
        master: Any,
        kullanici_id: int,
        notify: NotificationService,
        social: SocialService,
        on_kapat: Callable[[], None],
        on_profil: Optional[Callable[[int], None]] = None,
        on_islem_sonrasi: Optional[Callable[[], None]] = None,
        toast_fn: Optional[Callable[..., None]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color=COLOR_BG_CARD, corner_radius=0, width=DRAWER_WIDTH, **kwargs)
        self._uid = int(kullanici_id)
        self._notify = notify
        self._social = social
        self._on_kapat = on_kapat
        self._on_profil = on_profil
        self._on_islem = on_islem_sonrasi
        self._toast = toast_fn

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ust = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, border_width=1, border_color=COLOR_BORDER)
        ust.grid(row=0, column=0, sticky="ew")
        ic = ctk.CTkFrame(ust, fg_color="transparent")
        ic.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(ic, text="Bildirimler", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        ctk.CTkButton(ic, text="✕", width=36, fg_color="transparent", command=self._kapat).pack(side="right")
        ctk.CTkButton(
            ic,
            text="Tümünü okundu",
            height=32,
            fg_color=COLOR_PRIMARY,
            command=self._tumunu_oku,
        ).pack(side="right", padx=(0, 8))

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=12, pady=12)
        self._yenile()

    def _toast_goster(self, msg: str, tip: str = "success") -> None:
        if self._toast:
            self._toast(msg, tip=tip)

    def _yenile(self) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()
        liste = self._notify.liste(self._uid)
        if not liste:
            ctk.CTkLabel(
                self._scroll,
                text="Henüz bildiriminiz yok.",
                text_color=COLOR_TEXT_MUTED,
                font=ctk.CTkFont(size=14),
            ).pack(pady=40)
            return
        for b in liste:
            self._kart(b)

    def _kart(self, b: dict[str, Any]) -> None:
        kart = ctk.CTkFrame(
            self._scroll,
            fg_color=COLOR_BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        kart.pack(fill="x", pady=6)
        okundu = bool(int(b.get("okundu") or 0))
        ctk.CTkLabel(
            kart,
            text=f"{'● ' if not okundu else ''}{b.get('baslik')}",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(
            kart,
            text=str(b.get("mesaj") or ""),
            wraplength=320,
            justify="left",
            text_color=COLOR_TEXT_MUTED,
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", padx=12, pady=(0, 8))

        tip = str(b.get("tip") or "")
        kid = b.get("ilgili_kayit_id")
        uid = b.get("ilgili_kullanici_id")
        btn_row = ctk.CTkFrame(kart, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0, 10))

        if uid and self._on_profil:
            ctk.CTkButton(
                btn_row,
                text="Profili gör",
                width=100,
                height=30,
                fg_color="transparent",
                border_width=1,
                command=lambda u=int(uid): self._profil_git(u),
            ).pack(side="left", padx=2)

        if tip == config.BILDIRIM_TIP_EKIP_DAVET and kid:
            ctk.CTkButton(
                btn_row,
                text="Kabul",
                width=70,
                height=30,
                fg_color=COLOR_SUCCESS,
                command=lambda d=int(kid): self._davet_kabul(d),
            ).pack(side="left", padx=2)
            ctk.CTkButton(
                btn_row,
                text="Reddet",
                width=70,
                height=30,
                fg_color="transparent",
                border_width=1,
                command=lambda d=int(kid): self._davet_red(d),
            ).pack(side="left", padx=2)
        elif tip == config.BILDIRIM_TIP_KATILIM_ISTEGI and kid:
            ctk.CTkButton(
                btn_row,
                text="Onayla",
                width=80,
                height=30,
                fg_color=COLOR_PRIMARY,
                command=lambda i=int(kid): self._katilim_onay(i),
            ).pack(side="left", padx=2)
            ctk.CTkButton(
                btn_row,
                text="Reddet",
                width=70,
                height=30,
                fg_color="transparent",
                border_width=1,
                command=lambda i=int(kid): self._katilim_red(i),
            ).pack(side="left", padx=2)

        bid = int(b["id"])
        ctk.CTkButton(
            btn_row,
            text="Okundu",
            width=70,
            height=30,
            fg_color="transparent",
            command=lambda x=bid: self._okundu_isaretle(x),
        ).pack(side="right", padx=2)

    def _profil_git(self, kullanici_id: int) -> None:
        if self._on_profil:
            self._on_profil(kullanici_id)
            self._kapat()

    def _davet_kabul(self, davet_id: int) -> None:
        sonuc = self._social.davet_kabul(davet_id, self._uid)
        self._toast_goster(sonuc.mesaj, "success" if sonuc.basarili else "warning")
        if sonuc.basarili and self._on_islem:
            self._on_islem()
        self._yenile()

    def _davet_red(self, davet_id: int) -> None:
        sonuc = self._social.davet_reddet(davet_id, self._uid)
        self._toast_goster(sonuc.mesaj, "info" if sonuc.basarili else "warning")
        self._yenile()

    def _katilim_onay(self, istek_id: int) -> None:
        sonuc = self._social.katilim_onayla(istek_id, self._uid, config.ROL_SISTEM_ANALISTI)
        self._toast_goster(sonuc.mesaj, "success" if sonuc.basarili else "warning")
        if sonuc.basarili and self._on_islem:
            self._on_islem()
        self._yenile()

    def _katilim_red(self, istek_id: int) -> None:
        sonuc = self._social.katilim_reddet(istek_id, self._uid)
        self._toast_goster(sonuc.mesaj, "info" if sonuc.basarili else "warning")
        self._yenile()

    def _okundu_isaretle(self, bildirim_id: int) -> None:
        self._notify.okundu(bildirim_id, self._uid)
        if self._on_islem:
            self._on_islem()
        self._yenile()

    def _tumunu_oku(self) -> None:
        self._notify.tumunu_okundu(self._uid)
        if self._on_islem:
            self._on_islem()
        self._kapat()

    def _kapat(self) -> None:
        self._on_kapat()


def bildirim_cekmecesi_goster(
    host: ctk.CTkFrame,
    kullanici_id: int,
    notify: NotificationService,
    social: SocialService,
    on_kapat: Callable[[], None],
    on_profil: Optional[Callable[[int], None]] = None,
    on_islem_sonrasi: Optional[Callable[[], None]] = None,
    toast_fn: Optional[Callable[..., None]] = None,
) -> NotificationsDrawer:
    for w in host.winfo_children():
        if getattr(w, "_taskist_overlay", False):
            w.destroy()

    from src.ui.theme import COLOR_OVERLAY_SCRIM

    overlay = ctk.CTkFrame(host, fg_color=COLOR_OVERLAY_SCRIM)
    overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
    overlay.bind("<Button-1>", lambda e: _cekmecesi_kapat(overlay, on_kapat) if e.widget == overlay else None)
    overlay._taskist_overlay = True  # type: ignore[attr-defined]
    overlay.lift()

    drawer = NotificationsDrawer(
        overlay,
        kullanici_id,
        notify,
        social,
        on_kapat=lambda: _cekmecesi_kapat(overlay, on_kapat),
        on_profil=on_profil,
        on_islem_sonrasi=on_islem_sonrasi,
        toast_fn=toast_fn,
    )
    drawer.place(relx=1.0, rely=0, relheight=1, anchor="ne")
    drawer.lift()
    return drawer


def _cekmecesi_kapat(overlay: ctk.CTkFrame, on_kapat: Callable[[], None]) -> None:
    try:
        overlay.destroy()
    except Exception:
        pass
    on_kapat()
