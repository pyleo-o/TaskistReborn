# -*- coding: utf-8 -*-
"""teams_view.py — Ana sayfa (LinkedIn feed + ekip kartları)."""

from __future__ import annotations

from typing import Any, Callable, Optional

import customtkinter as ctk

from src.services.features_service import FeaturesService
from src.services.profile_service import ProfileService
from src.services.social_service import SocialService
from src.ui.components.empty_state import bos_durum_karti
import src.config as config
from src.services.workspace_service import WorkspaceService
from src.ui.components.avatar import AvatarWidget
from src.ui.theme import (
    COLOR_BG_APP,
    COLOR_BG_CARD,
    COLOR_BG_MUTED,
    COLOR_BORDER,
    COLOR_COVER,
    COLOR_PRIMARY,
    COLOR_TEXT_MUTED,
    btn_primary,
    btn_secondary,
    font_baslik,
    font_govde,
    font_kucuk,
    label_field,
    surface_card,
)
from src.ui.tooltip import tooltip_ekle


class TeamsView(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkFrame,
        kullanici: dict[str, Any],
        workspace_service: WorkspaceService,
        on_ekip_secildi: Callable[[int, str, str], None],
        on_cikis: Callable[[], None],
        social_service: Optional[SocialService] = None,
        toast_fn: Optional[Callable[..., None]] = None,
        on_kullanici_ara: Optional[Callable[[int], None]] = None,
        profile_service: Optional[ProfileService] = None,
        on_profil: Optional[Callable[[], None]] = None,
        features_service: Optional[FeaturesService] = None,
        on_dm: Optional[Callable[[int], None]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color=COLOR_BG_APP, **kwargs)
        self._user = kullanici
        self._ws = workspace_service
        self._social = social_service or SocialService()
        self._profiles = profile_service or ProfileService()
        self._feed_kutu: Optional[ctk.CTkFrame] = None
        self._kesfet_kutu: Optional[ctk.CTkFrame] = None
        self._on_select = on_ekip_secildi
        self._toast_fn = toast_fn
        self._on_kullanici_ara = on_kullanici_ara
        self._on_profil = on_profil
        self._feat = features_service or FeaturesService()
        self._on_dm = on_dm
        self._build()

    def _toast(self, msg: str, tip: str = "success") -> None:
        if self._toast_fn:
            self._toast_fn(msg, tip=tip)

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=0, minsize=280)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0, minsize=300)
        self.grid_rowconfigure(0, weight=1)

        sol = ctk.CTkScrollableFrame(self, fg_color="transparent", width=260)
        sol.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)

        prof_kart = surface_card(sol)
        prof_kart.pack(fill="x", pady=(0, 12))
        cover = ctk.CTkFrame(prof_kart, height=44, fg_color=COLOR_COVER, corner_radius=12)
        cover.pack(fill="x", padx=0, pady=0)
        cover.pack_propagate(False)
        govde_prof = ctk.CTkFrame(prof_kart, fg_color="transparent")
        govde_prof.pack(fill="x", padx=12, pady=(0, 10))
        av_sat = ctk.CTkFrame(govde_prof, fg_color="transparent")
        av_sat.pack(fill="x", pady=(8, 6))
        AvatarWidget(
            av_sat, int(self._user["id"]), self._user.get("avatar_yolu"), boyut=52, yuvarlak=True
        ).pack(anchor="w")
        ad = self._user.get("ad_soyad") or self._user.get("email")
        ctk.CTkLabel(govde_prof, text=ad, font=font_baslik(15)).pack(anchor="w")
        kadi = self._user.get("kullanici_adi") or ""
        if kadi:
            ctk.CTkLabel(govde_prof, text=f"@{kadi}", text_color=COLOR_TEXT_MUTED, font=font_kucuk()).pack(
                anchor="w", pady=(0, 6)
            )
        if self._on_profil:
            btn_secondary(govde_prof, "Profilim", command=self._on_profil, height=34).pack(
                fill="x", pady=(0, 4)
            )

        ctk.CTkLabel(sol, text="Gezinme", font=font_baslik(13)).pack(anchor="w", pady=(8, 6))

        self._orta_wrap = ctk.CTkFrame(self, fg_color="transparent")
        self._orta_wrap.grid(row=0, column=1, sticky="nsew", padx=8, pady=16)
        self._orta_wrap.grid_rowconfigure(1, weight=1)
        self._orta_wrap.grid_columnconfigure(0, weight=1)

        hos = surface_card(self._orta_wrap)
        hos.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        h_sat = ctk.CTkFrame(hos, fg_color="transparent")
        h_sat.pack(fill="x", padx=16, pady=12)
        ctk.CTkLabel(
            h_sat,
            text=f"Merhaba, {(ad or '').split()[0] or 'ekip üyesi'}! 👋",
            font=font_baslik(18),
        ).pack(side="left")
        btn_ekip = btn_primary(h_sat, "+ Yeni ekip", command=self._yeni_ekip_tikla, width=120, height=36)
        btn_ekip.pack(side="right")
        tooltip_ekle(btn_ekip, "yeni_ekip")

        self._tabs = ctk.CTkTabview(self._orta_wrap, fg_color=COLOR_BG_CARD)
        self._tabs.grid(row=1, column=0, sticky="nsew")

        tab_akis = self._tabs.add("Akış")
        tab_ekip = self._tabs.add("Çalışma alanları")
        tab_kesfet = self._tabs.add("Keşfet")

        scroll_akis = ctk.CTkScrollableFrame(tab_akis, fg_color="transparent")
        scroll_akis.pack(fill="both", expand=True, padx=4, pady=4)

        paylas = surface_card(scroll_akis)
        paylas.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(paylas, text="Gönderi paylaş", font=font_baslik(14)).pack(anchor="w", padx=16, pady=(12, 6))
        self._txt_gonderi = ctk.CTkTextbox(paylas, height=72)
        self._txt_gonderi.pack(fill="x", padx=16, pady=(0, 8))
        gor_sat = ctk.CTkFrame(paylas, fg_color="transparent")
        gor_sat.pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(gor_sat, text="Görünürlük", font=font_kucuk()).pack(side="left")
        self._opt_gorunurluk = ctk.CTkOptionMenu(
            gor_sat,
            values=["herkes", "baglanti", "ekip", "gizli"],
            width=140,
        )
        self._opt_gorunurluk.set("herkes")
        self._opt_gorunurluk.pack(side="right")
        btn_primary(paylas, "Paylaş", command=self._gonderi_paylas, height=36).pack(
            anchor="e", padx=16, pady=(0, 12)
        )
        self._feed_kutu = ctk.CTkFrame(scroll_akis, fg_color="transparent")
        self._feed_kutu.pack(fill="x")

        scroll_ekip = ctk.CTkScrollableFrame(tab_ekip, fg_color="transparent")
        scroll_ekip.pack(fill="both", expand=True, padx=4, pady=4)
        self._ekip_kutu = ctk.CTkFrame(scroll_ekip, fg_color="transparent")
        self._ekip_kutu.pack(fill="x")

        scroll_kesfet = ctk.CTkScrollableFrame(tab_kesfet, fg_color="transparent")
        scroll_kesfet.pack(fill="both", expand=True, padx=4, pady=4)
        self._kesfet_kutu = ctk.CTkFrame(scroll_kesfet, fg_color="transparent")
        self._kesfet_kutu.pack(fill="x")

        for metin, sekme in (
            ("📰 Akış", "Akış"),
            ("👥 Ekiplerim", "Çalışma alanları"),
            ("🔍 Keşfet", "Keşfet"),
        ):
            btn_secondary(sol, metin, command=lambda s=sekme: self._sekme_ac(s), height=34, anchor="w").pack(
                fill="x", pady=2
            )

        sag = ctk.CTkFrame(self, fg_color="transparent", width=300)
        sag.grid(row=0, column=2, sticky="nsew", padx=(8, 16), pady=16)

        sag_tabs = ctk.CTkTabview(sag, fg_color=COLOR_BG_CARD)
        sag_tabs.pack(fill="both", expand=True)
        t_ara = sag_tabs.add("Ara")
        t_oneri = sag_tabs.add("Öneriler")
        t_davet = sag_tabs.add("Davetler")
        t_ipucu = sag_tabs.add("İpuçları")

        self._arama_k = surface_card(t_ara)
        self._arama_k.pack(fill="both", expand=True, padx=4, pady=4)
        label_field(self._arama_k, "Kişi ara").pack(anchor="w", padx=12, pady=(12, 4))
        self._ent_ara = ctk.CTkEntry(self._arama_k, placeholder_text="@kullanici veya e-posta", height=38)
        self._ent_ara.pack(fill="x", padx=12, pady=(0, 8))
        btn_ara = btn_primary(self._arama_k, "Ara", command=self._ara_tikla, height=34)
        btn_ara.pack(fill="x", padx=12, pady=(0, 8))
        tooltip_ekle(btn_ara, "kullanici_ara")
        self._sonuc_kutu = ctk.CTkScrollableFrame(self._arama_k, fg_color="transparent", height=200)
        self._sonuc_kutu.pack(fill="both", expand=True, padx=8, pady=(0, 12))

        oneri_wrap = ctk.CTkFrame(t_oneri, fg_color="transparent")
        oneri_wrap.pack(fill="both", expand=True, padx=4, pady=4)
        self._oneri_kutu = ctk.CTkScrollableFrame(oneri_wrap, fg_color="transparent")
        self._oneri_kutu.pack(fill="both", expand=True)

        davet_wrap = ctk.CTkFrame(t_davet, fg_color="transparent")
        davet_wrap.pack(fill="both", expand=True, padx=4, pady=4)
        self._davet_kutu = ctk.CTkScrollableFrame(davet_wrap, fg_color="transparent")
        self._davet_kutu.pack(fill="both", expand=True)

        ipucu = surface_card(t_ipucu)
        ipucu.pack(fill="both", expand=True, padx=4, pady=4)
        ctk.CTkLabel(ipucu, text="Taskist ipuçları", font=font_baslik(14)).pack(anchor="w", padx=14, pady=(14, 8))
        for ip in (
            "Üst çubuktan global arama (Ctrl+F).",
            "Kritik görevler panoda üstte görünür.",
            "Ctrl+M mesajlar, Ctrl+H ana sayfa.",
        ):
            ctk.CTkLabel(
                ipucu, text=f"• {ip}", wraplength=240, justify="left", text_color=COLOR_TEXT_MUTED, font=font_kucuk()
            ).pack(anchor="w", padx=14, pady=2)

        self._listeyi_yenile()
        self._feed_yenile()
        self._kesfet_yenile()
        self._davetleri_yenile()
        self._onerileri_yenile()

    def _onerileri_yenile(self) -> None:
        if not hasattr(self, "_oneri_kutu"):
            return
        for w in self._oneri_kutu.winfo_children():
            w.destroy()
        try:
            oneriler = self._feat.baglanti_onerileri(int(self._user["id"]), 5)
        except Exception:
            oneriler = []
        if not oneriler:
            ctk.CTkLabel(
                self._oneri_kutu,
                text="Şimdilik öneri yok.",
                text_color=COLOR_TEXT_MUTED,
                font=ctk.CTkFont(size=11),
            ).pack(anchor="w", padx=4)
            return
        for o in oneriler:
            sat = ctk.CTkFrame(self._oneri_kutu, fg_color="transparent")
            sat.pack(fill="x", pady=3)
            ad = o.get("ad_soyad") or o.get("kullanici_adi") or "?"
            uid = int(o["id"])
            ctk.CTkLabel(sat, text=ad[:22], font=ctk.CTkFont(size=12)).pack(side="left")

            def _profil(hedef=uid) -> None:
                if self._on_kullanici_ara:
                    self._on_kullanici_ara(hedef)

            ctk.CTkButton(sat, text="Profil", width=56, height=26, command=_profil).pack(side="right", padx=2)
            if self._on_dm:

                def _dm(hedef=uid) -> None:
                    self._on_dm(hedef)

                ctk.CTkButton(sat, text="Mesaj", width=56, height=26, command=_dm).pack(side="right")

    def _gonderi_paylas(self) -> None:
        metin = self._txt_gonderi.get("1.0", "end").strip()
        gor = self._opt_gorunurluk.get()
        sonuc = self._social.gonderi_paylas(int(self._user["id"]), metin, gorunurluk=gor)
        if sonuc.basarili:
            self._txt_gonderi.delete("1.0", "end")
            self._toast(sonuc.mesaj)
            self._feed_yenile()
        else:
            self._toast(sonuc.mesaj, tip="warning")

    def _feed_yenile(self) -> None:
        if not self._feed_kutu:
            return
        for w in self._feed_kutu.winfo_children():
            w.destroy()
        try:
            gonderiler = self._social.feed_listele(int(self._user["id"]))
        except Exception as ex:
            ctk.CTkLabel(self._feed_kutu, text=str(ex), text_color=COLOR_TEXT_MUTED).pack()
            return
        if not gonderiler:
            bos_durum_karti(
                self._feed_kutu,
                "📰",
                "Akış boş",
                "Paylaşım yapın veya kişileri takip edin.",
                cta_metin="İlk gönderiyi yaz",
                cta_command=lambda: self._txt_gonderi.focus_set(),
            ).pack(fill="x", pady=8)
            return
        for g in gonderiler[:15]:
            kart = surface_card(self._feed_kutu)
            kart.pack(fill="x", pady=4)
            ust = ctk.CTkFrame(kart, fg_color="transparent")
            ust.pack(fill="x", padx=12, pady=(10, 4))
            AvatarWidget(ust, int(g["yazar_id"]), g.get("avatar_yolu"), boyut=36, yuvarlak=True).pack(side="left")
            ad = g.get("ad_soyad") or g.get("kullanici_adi") or "?"
            ctk.CTkLabel(ust, text=ad, font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=8)
            if g.get("ekip_ad"):
                ctk.CTkLabel(ust, text=f"· {g['ekip_ad']}", text_color=COLOR_TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(
                kart,
                text=str(g.get("icerik") or ""),
                wraplength=500,
                justify="left",
            ).pack(anchor="w", padx=12, pady=(0, 6))
            alt = ctk.CTkFrame(kart, fg_color="transparent")
            alt.pack(fill="x", padx=10, pady=(0, 8))
            gid = int(g["id"])
            begeni = int(g.get("begeni_sayisi") or 0)
            begendim = bool(g.get("begendim"))

            def _begeni(toggle_id=gid) -> None:
                self._social.begeni_toggle(toggle_id, int(self._user["id"]))
                self._feed_yenile()

            ctk.CTkButton(
                alt,
                text=f"{'♥' if begendim else '♡'} {begeni}",
                width=80,
                height=28,
                fg_color="transparent",
                command=_begeni,
            ).pack(side="left")

    def _kesfet_yenile(self) -> None:
        if not self._kesfet_kutu:
            return
        for w in self._kesfet_kutu.winfo_children():
            w.destroy()
        try:
            ekipler = self._social.kesfedilebilir_ekipler(int(self._user["id"]))
        except Exception as ex:
            ctk.CTkLabel(self._kesfet_kutu, text=str(ex), text_color=COLOR_TEXT_MUTED).pack()
            return
        if not ekipler:
            ctk.CTkLabel(
                self._kesfet_kutu,
                text="Şu an keşfedilecek yeni ekip yok.",
                text_color=COLOR_TEXT_MUTED,
            ).pack(anchor="w", pady=6)
            return
        for e in ekipler[:6]:
            eid = int(e["ekip_id"])
            kart = ctk.CTkFrame(
                self._kesfet_kutu,
                fg_color=COLOR_BG_CARD,
                corner_radius=10,
                border_width=1,
                border_color=COLOR_BORDER,
            )
            kart.pack(fill="x", pady=4)
            ctk.CTkLabel(kart, text=str(e.get("ekip_ad")), font=ctk.CTkFont(weight="bold")).pack(
                anchor="w", padx=12, pady=(8, 2)
            )
            ol = e.get("olusturan_kadi") or e.get("olusturan_ad") or ""
            ctk.CTkLabel(
                kart,
                text=f"@{ol} · {e.get('uye_sayisi', 0)} üye",
                text_color=COLOR_TEXT_MUTED,
                font=ctk.CTkFont(size=11),
            ).pack(anchor="w", padx=12)

            def _istek(ekip=eid) -> None:
                dlg = ctk.CTkInputDialog(text="Kısa mesaj (opsiyonel):", title="Katılma isteği")
                msg = (dlg.get_input() or "").strip()
                sonuc = self._social.katilim_istegi_gonder(ekip, int(self._user["id"]), msg)
                self._toast(sonuc.mesaj, "success" if sonuc.basarili else "warning")

            ctk.CTkButton(kart, text="Katılma isteği gönder", height=32, command=_istek).pack(
                fill="x", padx=12, pady=(6, 10)
            )

    def _davetleri_yenile(self) -> None:
        if not hasattr(self, "_davet_kutu"):
            return
        for w in self._davet_kutu.winfo_children():
            w.destroy()
        try:
            davetler = self._social.bekleyen_davetler(int(self._user["id"]))
        except Exception:
            return
        if not davetler:
            ctk.CTkLabel(
                self._davet_kutu,
                text="Bekleyen davet yok.",
                text_color=COLOR_TEXT_MUTED,
                font=ctk.CTkFont(size=11),
            ).pack(anchor="w")
            return
        for d in davetler[:5]:
            sat = ctk.CTkFrame(self._davet_kutu, fg_color=COLOR_BG_MUTED, corner_radius=8)
            sat.pack(fill="x", pady=3)
            ctk.CTkLabel(
                sat,
                text=f"{d.get('ekip_ad')} ({d.get('rol_adi')})",
                font=ctk.CTkFont(size=11, weight="bold"),
                wraplength=220,
            ).pack(anchor="w", padx=8, pady=(6, 2))
            br = ctk.CTkFrame(sat, fg_color="transparent")
            br.pack(fill="x", padx=6, pady=(0, 6))
            did = int(d["id"])

            def _kabul(davet_id=did) -> None:
                s = self._social.davet_kabul(davet_id, int(self._user["id"]))
                self._toast(s.mesaj, "success" if s.basarili else "warning")
                self._davetleri_yenile()
                self._listeyi_yenile()

            ctk.CTkButton(br, text="Kabul", width=60, height=26, fg_color=COLOR_PRIMARY, command=_kabul).pack(
                side="left", padx=2
            )

    def _sekme_ac(self, ad: str) -> None:
        try:
            self._tabs.set(ad)
        except Exception:
            pass

    def _ekiplerim_git(self) -> None:
        self._sekme_ac("Çalışma alanları")

    def _ara_tikla(self) -> None:
        for w in self._sonuc_kutu.winfo_children():
            w.destroy()
        try:
            sonuclar = self._profiles.ara(self._ent_ara.get())
        except Exception as ex:
            self._toast(str(ex), tip="error")
            return
        if not sonuclar:
            ctk.CTkLabel(self._sonuc_kutu, text="Sonuç yok", text_color=COLOR_TEXT_MUTED).pack(anchor="w")
            return
        for u in sonuclar[:6]:
            uid = int(u["id"])
            sat = ctk.CTkFrame(self._sonuc_kutu, fg_color=COLOR_BG_MUTED, corner_radius=8)
            sat.pack(fill="x", pady=3)
            AvatarWidget(sat, uid, u.get("avatar_yolu"), boyut=32).pack(side="left", padx=6, pady=6)
            kadi = u.get("kullanici_adi") or "?"
            ctk.CTkLabel(sat, text=f"@{kadi}", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")

            def _p(hedef=uid) -> None:
                if self._on_kullanici_ara:
                    self._on_kullanici_ara(hedef)

            ctk.CTkButton(sat, text="→", width=32, fg_color="transparent", command=_p).pack(side="right", padx=4)

    def _yeni_ekip_tikla(self) -> None:
        dlg = ctk.CTkInputDialog(text="Ekip adı:", title="Yeni Ekip")
        ad = dlg.get_input()
        if not ad or not str(ad).strip():
            return
        ac = (ctk.CTkInputDialog(text="Açıklama (opsiyonel):", title="Açıklama").get_input() or "").strip()
        try:
            sonuc = self._ws.yeni_ekip_olustur(int(self._user["id"]), str(ad).strip(), ac)
        except Exception as ex:
            self._toast(str(ex), tip="error")
            return
        if not sonuc.basarili:
            self._toast(sonuc.mesaj, tip="warning")
            return
        self._toast("Ekip oluşturuldu.")
        self._listeyi_yenile()

    def _listeyi_yenile(self) -> None:
        for w in self._ekip_kutu.winfo_children():
            w.destroy()
        try:
            satirlar = self._ws.ekiplerimi_listele(int(self._user["id"]))
        except Exception as ex:
            self._toast(str(ex), tip="error")
            return
        if not satirlar:
            bos_durum_karti(
                self._ekip_kutu,
                "👥",
                "Henüz ekip yok",
                "Üstten yeni ekip oluşturun.",
                cta_metin="+ Yeni ekip",
                cta_command=self._yeni_ekip_tikla,
            ).pack(fill="x", pady=12)
            return
        grid = ctk.CTkFrame(self._ekip_kutu, fg_color="transparent")
        grid.pack(fill="x")
        for i, row in enumerate(satirlar):
            self._ekip_karti(grid, row, i)

    def _ekip_karti(self, parent: ctk.CTkFrame, row: dict[str, Any], idx: int) -> None:
        ekip_id = int(row["ekip_id"])
        ekip_ad = str(row["ekip_ad"])
        rol = str(row["rol_adi"])
        kart = surface_card(parent)
        kart.grid(row=idx // 2, column=idx % 2, padx=6, pady=6, sticky="nsew")
        parent.grid_columnconfigure(idx % 2, weight=1)

        baslik = ctk.CTkFrame(kart, height=8, fg_color=COLOR_PRIMARY, corner_radius=12)
        baslik.pack(fill="x")
        baslik.pack_propagate(False)
        ctk.CTkLabel(kart, text=ekip_ad, font=ctk.CTkFont(size=17, weight="bold")).pack(
            anchor="w", padx=16, pady=(14, 4)
        )
        ctk.CTkLabel(kart, text=f"Rolünüz: {rol}", text_color=COLOR_PRIMARY).pack(anchor="w", padx=16)
        ac = (row.get("ekip_aciklama") or "").strip()
        if ac:
            ctk.CTkLabel(kart, text=ac[:120], wraplength=280, text_color=COLOR_TEXT_MUTED).pack(
                anchor="w", padx=16, pady=8
            )
        btn = btn_primary(
            kart,
            "Panele git →",
            height=38,
            command=lambda: self._on_select(ekip_id, ekip_ad, rol),
        )
        btn.pack(fill="x", padx=16, pady=(8, 16))
        tooltip_ekle(btn, "ekibe_gir")
