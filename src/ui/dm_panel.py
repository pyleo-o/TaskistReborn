# -*- coding: utf-8 -*-
"""dm_panel.py — Doğrudan mesaj çekmecesi."""

from __future__ import annotations

from typing import Any, Callable, Optional

import customtkinter as ctk

from src.repositories.features_repository import FeaturesRepository
from src.services.features_service import FeaturesService
from src.ui.components.avatar import AvatarWidget
from src.ui.components.ui_widgets import drawer_overlay
from src.ui.theme import (
    COLOR_BG_MUTED,
    COLOR_PRIMARY,
    COLOR_TEXT_MUTED,
    DRAWER_WIDTH,
    btn_primary,
    font_govde,
)


def dm_cekmecesi_goster(
    master: ctk.CTkFrame,
    kullanici: dict[str, Any],
    features: FeaturesService,
    on_kapat: Optional[Callable[[], None]] = None,
    on_profil: Optional[Callable[[int], None]] = None,
    toast_fn: Optional[Callable[..., None]] = None,
    hedef_id: Optional[int] = None,
) -> ctk.CTkFrame:
    """Sağdan açılan DM paneli; hedef_id verilirse doğrudan sohbet açar."""
    repo = FeaturesRepository()
    uid = int(kullanici["id"])
    features.heartbeat(uid)

    def _kapat() -> None:
        if on_kapat:
            on_kapat()

    overlay, icerik = drawer_overlay(master, "Mesajlar", _kapat)
    panel = overlay.winfo_children()[0] if overlay.winfo_children() else overlay
    try:
        panel.configure(width=DRAWER_WIDTH)
    except Exception:
        pass

    sohbet_host = ctk.CTkScrollableFrame(icerik, fg_color="transparent", label_text="Sohbetler")
    sohbet_host.pack(fill="both", expand=True, padx=8, pady=4)

    chat_host = ctk.CTkFrame(icerik, fg_color="transparent")
    aktif_sohbet: list[Optional[int]] = [None]
    aktif_karsi: list[Optional[int]] = [None]

    def _sohbet_listesi() -> None:
        for w in sohbet_host.winfo_children():
            w.destroy()
        sohbet_host.pack(fill="both", expand=True)
        chat_host.pack_forget()
        liste = repo.sohbet_listesi(uid)
        if not liste:
            ctk.CTkLabel(
                sohbet_host,
                text="Henüz mesajınız yok.\nBir profilden «Mesaj» ile başlayın.",
                text_color=COLOR_TEXT_MUTED,
                justify="center",
            ).pack(pady=40)
            return
        for s in liste:
            sid = int(s["sohbet_id"])
            kid = int(s["karsi_id"])

            def _ac(sid=sid, kid=kid) -> None:
                _sohbet_ac(sid, kid)

            sat = ctk.CTkFrame(sohbet_host, fg_color=COLOR_BG_MUTED, corner_radius=8)
            sat.pack(fill="x", pady=4)
            sat.bind("<Button-1>", lambda _e, fn=_ac: fn())
            r = ctk.CTkFrame(sat, fg_color="transparent")
            r.pack(fill="x", padx=8, pady=8)
            AvatarWidget(r, kid, s.get("avatar_yolu"), boyut=36, yuvarlak=True).pack(side="left")
            ad = s.get("ad_soyad") or s.get("kullanici_adi") or "?"
            ctk.CTkLabel(r, text=ad, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=8)
            durum = features.presence_metni(kid)
            ctk.CTkLabel(r, text=durum, text_color=COLOR_TEXT_MUTED, font=ctk.CTkFont(size=10)).pack(
                anchor="w", padx=52
            )
            if s.get("son_mesaj"):
                ctk.CTkLabel(
                    r,
                    text=str(s["son_mesaj"])[:60],
                    text_color=COLOR_TEXT_MUTED,
                    font=ctk.CTkFont(size=11),
                ).pack(anchor="w", padx=52, pady=(0, 4))

    def _sohbet_ac(sohbet_id: int, karsi_id: int) -> None:
        aktif_sohbet[0] = sohbet_id
        aktif_karsi[0] = karsi_id
        sohbet_host.pack_forget()
        for w in chat_host.winfo_children():
            w.destroy()
        chat_host.pack(fill="both", expand=True)

        bas = ctk.CTkFrame(chat_host, fg_color="transparent")
        bas.pack(fill="x", padx=8, pady=4)
        ctk.CTkButton(bas, text="←", width=36, fg_color="transparent", command=_sohbet_listesi).pack(
            side="left"
        )
        ad = ""
        k = repo.presence_getir(karsi_id)
        for s in repo.sohbet_listesi(uid):
            if int(s.get("karsi_id") or 0) == karsi_id:
                ad = s.get("ad_soyad") or s.get("kullanici_adi") or ""
                break
        ctk.CTkLabel(bas, text=ad, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=4)
        ctk.CTkLabel(
            bas,
            text=features.presence_metni(karsi_id),
            text_color=COLOR_TEXT_MUTED,
            font=ctk.CTkFont(size=11),
        ).pack(side="left")

        if on_profil:

            def _profil() -> None:
                _kapat()
                on_profil(karsi_id)

            ctk.CTkButton(bas, text="Profil", width=60, height=28, command=_profil).pack(side="right")

        msg_box = ctk.CTkScrollableFrame(chat_host, fg_color="transparent")
        msg_box.pack(fill="both", expand=True, padx=8, pady=4)
        for m in repo.mesajlari_listele(sohbet_id):
            benim = int(m["gonderen_id"]) == uid
            f = ctk.CTkFrame(
                msg_box,
                fg_color=COLOR_PRIMARY if benim else COLOR_BG_MUTED,
                corner_radius=12,
            )
            f.pack(anchor="e" if benim else "w", pady=3, padx=4)
            ctk.CTkLabel(f, text=str(m.get("icerik") or ""), wraplength=300, justify="left").pack(
                padx=10, pady=8
            )

        alt = ctk.CTkFrame(chat_host, fg_color="transparent")
        alt.pack(fill="x", padx=8, pady=8)
        ent = ctk.CTkEntry(alt, placeholder_text="Mesaj yazın…")
        ent.pack(side="left", fill="x", expand=True, padx=(0, 6))

        def _gonder() -> None:
            s = features.dm_gonder(uid, karsi_id, ent.get())
            if toast_fn:
                toast_fn(s.mesaj, tip="success" if s.basarili else "warning")
            if s.basarili:
                ent.delete(0, "end")
                _sohbet_ac(sohbet_id, karsi_id)

        btn_primary(alt, "Gönder", width=70, command=_gonder).pack(side="right")
        ent.bind("<Return>", lambda _e: _gonder())

    _sohbet_listesi()
    if hedef_id is not None and int(hedef_id) != uid:
        sid = repo.sohbet_bul_veya_olustur(uid, int(hedef_id))
        _sohbet_ac(sid, int(hedef_id))

    return overlay
