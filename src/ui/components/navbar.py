# -*- coding: utf-8 -*-
"""navbar.py — İkonlu üst gezinme, arama, badge."""

from __future__ import annotations

from typing import Any, Callable, Optional

import customtkinter as ctk

import src.config as config
from src.ui.components.avatar import AvatarWidget
from src.ui.components.ui_widgets import NavIconButton
from src.ui.theme import (
    COLOR_BG_CARD,
    COLOR_BORDER,
    COLOR_PRIMARY,
    NAVBAR_HEIGHT,
    NavSayfa,
    btn_ghost,
    entry_field,
    font_baslik,
)
from src.ui.tooltip import tooltip_ekle


class AppNavbar(ctk.CTkFrame):
    def __init__(
        self,
        master: Any,
        kullanici: Optional[dict[str, Any]],
        okunmamis: int = 0,
        aktif_sayfa: NavSayfa = "ana",
        on_profil: Optional[Callable[[], None]] = None,
        on_bildirim: Optional[Callable[[], None]] = None,
        on_dm: Optional[Callable[[], None]] = None,
        on_ana_sayfa: Optional[Callable[[], None]] = None,
        on_ara: Optional[Callable[[str], None]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            master,
            height=NAVBAR_HEIGHT,
            corner_radius=0,
            fg_color=COLOR_BG_CARD,
            border_width=1,
            border_color=COLOR_BORDER,
            **kwargs,
        )
        self.pack_propagate(False)
        self.grid_columnconfigure(1, weight=1)

        sol = ctk.CTkFrame(self, fg_color="transparent")
        sol.grid(row=0, column=0, padx=(12, 8), pady=8, sticky="w")

        logo = ctk.CTkButton(
            sol,
            text="T",
            width=40,
            height=40,
            corner_radius=10,
            fg_color=COLOR_PRIMARY,
            hover_color="#004182",
            font=ctk.CTkFont(size=22, weight="bold"),
            command=on_ana_sayfa or (lambda: None),
        )
        logo.pack(side="left")
        tooltip_ekle(logo, "geri_ekipler")
        ctk.CTkLabel(sol, text=config.UI_APP_TITLE, font=font_baslik(15)).pack(side="left", padx=(10, 0))

        orta = ctk.CTkFrame(self, fg_color="transparent")
        orta.grid(row=0, column=1, sticky="ew", padx=8)
        self._ent_ara = entry_field(orta, placeholder="Ara (@kullanici veya e-posta) — Enter")
        self._ent_ara.pack(fill="x", ipady=2)
        if on_ara:
            self._ent_ara.bind("<Return>", lambda _e: on_ara(self._ent_ara.get().strip()))

        sag = ctk.CTkFrame(self, fg_color="transparent")
        sag.grid(row=0, column=2, padx=12, pady=8, sticky="e")

        if on_ana_sayfa:
            NavIconButton(
                sag, "🏠", command=on_ana_sayfa, aktif=(aktif_sayfa == "ana")
            ).pack(side="left", padx=2)
        if on_dm:
            NavIconButton(sag, "💬", command=on_dm, aktif=(aktif_sayfa == "mesaj")).pack(
                side="left", padx=2
            )
        if on_bildirim:
            NavIconButton(
                sag,
                "🔔",
                command=on_bildirim,
                badge=okunmamis,
                aktif=(aktif_sayfa == "bildirim"),
            ).pack(side="left", padx=2)

        if kullanici and on_profil:
            af = ctk.CTkFrame(sag, fg_color="transparent")
            af.pack(side="left", padx=(8, 0))
            if aktif_sayfa == "profil":
                ctk.CTkFrame(af, height=3, fg_color=COLOR_PRIMARY, width=48).pack(side="bottom")
            av = AvatarWidget(af, int(kullanici["id"]), kullanici.get("avatar_yolu"), boyut=36, yuvarlak=True)
            av.pack(side="left")
            ad = (kullanici.get("ad_soyad") or kullanici.get("email", "")).split()[0]
            btn_p = btn_ghost(af, f" {ad} ", height=36, command=on_profil)
            btn_p.pack(side="left")
            tooltip_ekle(btn_p, "profilim")
