# -*- coding: utf-8 -*-
"""profile_view.py — Instagram tarzı profil görünümü + ayarlar çekmecesi."""

from __future__ import annotations

from typing import Any, Callable, Optional

import customtkinter as ctk

from src.repositories.features_repository import FeaturesRepository
from src.services.features_service import FeaturesService
from src.services.profile_service import ProfileService
from src.services.social_service import SocialService
from src.ui.components.empty_state import bos_durum_karti
from src.ui.components.avatar import AvatarWidget
from src.ui.profile_settings_panel import profil_ayarlari_goster
from src.ui.theme import (
    COLOR_ACCENT,
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
    online_dot,
    surface_card,
)
from src.ui.tooltip import tooltip_ekle


class ProfileView(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkFrame,
        kullanici: dict[str, Any],
        profile_service: ProfileService,
        on_geri: Callable[[], None],
        hedef_id: Optional[int] = None,
        toast_fn: Optional[Callable[..., None]] = None,
        on_takip_bildirim: Optional[Callable[[int, str, str], None]] = None,
        on_avatar_degisti: Optional[Callable[[], None]] = None,
        on_tema: Optional[Callable[[], None]] = None,
        on_cikis: Optional[Callable[[], None]] = None,
        tema_koyu: bool = True,
        social_service: Optional[SocialService] = None,
        features_service: Optional[FeaturesService] = None,
        on_dm: Optional[Callable[[int], None]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color=COLOR_BG_APP, **kwargs)
        self._user = kullanici
        self._svc = profile_service
        self._social = social_service or SocialService()
        self._feat = features_service or FeaturesService()
        self._feat_repo = FeaturesRepository()
        self._on_dm = on_dm
        self._on_geri = on_geri
        self._hedef_id = int(hedef_id) if hedef_id else int(kullanici["id"])
        self._toast = toast_fn
        self._on_takip_bildirim = on_takip_bildirim
        self._on_avatar_degisti = on_avatar_degisti
        self._on_tema = on_tema
        self._on_cikis = on_cikis
        self._tema_koyu = tema_koyu
        self._benim = self._hedef_id == int(kullanici["id"])
        self._profil: Optional[dict[str, Any]] = None
        self._avatar_w: Optional[AvatarWidget] = None
        self._icerik_host: Optional[ctk.CTkFrame] = None
        self._build()

    def _toast_goster(self, msg: str, tip: str = "success") -> None:
        if self._toast:
            self._toast(msg, tip=tip)

    def _build(self) -> None:
        ust = ctk.CTkFrame(self, fg_color="transparent", height=52)
        ust.pack(fill="x", padx=12, pady=(8, 0))
        ust.pack_propagate(False)

        ctk.CTkButton(ust, text="←", width=40, fg_color="transparent", command=self._on_geri).pack(
            side="left", pady=6
        )

        self._lbl_baslik = ctk.CTkLabel(ust, text="Profil", font=ctk.CTkFont(size=16, weight="bold"))
        self._lbl_baslik.pack(side="left", padx=8, pady=6)

        self._btn_ayar = ctk.CTkButton(
            ust,
            text="⚙",
            width=40,
            height=40,
            fg_color="transparent",
            font=ctk.CTkFont(size=22),
            command=self._ayarlari_ac,
        )

        self._icerik_host = ctk.CTkFrame(self, fg_color="transparent")
        self._icerik_host.pack(fill="both", expand=True)

        self._scroll = ctk.CTkScrollableFrame(self._icerik_host, fg_color=COLOR_BG_APP, label_text="")
        self._scroll.pack(fill="both", expand=True, padx=0, pady=0)
        self._yenile()

    def _ayarlari_ac(self) -> None:
        if not self._benim or not self._profil or not self._on_tema or not self._on_cikis:
            return
        assert self._icerik_host is not None

        def _guncellendi() -> None:
            self._tema_koyu = ctk.get_appearance_mode() == "Dark"
            if self._on_avatar_degisti:
                self._on_avatar_degisti()
            self._yenile()

        profil_ayarlari_goster(
            self._icerik_host,
            kullanici=self._user,
            profil=self._profil,
            profile_service=self._svc,
            tema_koyu=self._tema_koyu,
            on_tema=self._on_tema,
            on_cikis=self._on_cikis,
            on_guncellendi=_guncellendi,
            toast_fn=self._toast,
            features_service=self._feat,
        )

    def _yenile(self) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()
        try:
            self._profil = self._svc.profil_getir(self._hedef_id, int(self._user["id"]))
        except Exception as ex:
            ctk.CTkLabel(
                self._scroll,
                text=f"Profil yüklenemedi: {ex}",
                text_color=COLOR_TEXT_MUTED,
                wraplength=500,
            ).pack(pady=40, padx=24)
            return
        if not self._profil:
            ctk.CTkLabel(self._scroll, text="Profil bulunamadı.", text_color=COLOR_TEXT_MUTED).pack(pady=40)
            return

        kadi = self._profil.get("kullanici_adi") or ""
        self._lbl_baslik.configure(text=f"@{kadi}" if kadi else "Profil")

        if self._benim and self._on_tema and self._on_cikis:
            self._btn_ayar.pack(side="right", pady=4)
            tooltip_ekle(self._btn_ayar, "profil_ayarlar")
        else:
            self._btn_ayar.pack_forget()

        if self._profil.get("profil_gizli") and not self._benim:
            bos_durum_karti(
                self._scroll,
                "🔒",
                "Bu profil gizli",
                "Bu kullanıcı profilini gizledi.",
            ).pack(fill="x", padx=24, pady=60)
            return

        hero = surface_card(self._scroll)
        hero.pack(fill="x", padx=20, pady=(8, 0))
        cover = ctk.CTkFrame(hero, height=88, fg_color=COLOR_COVER, corner_radius=12)
        cover.pack(fill="x")
        cover.pack_propagate(False)

        govde = ctk.CTkFrame(hero, fg_color="transparent")
        govde.pack(fill="x", padx=16, pady=(0, 12))
        govde.grid_columnconfigure(0, weight=1)

        av_row = ctk.CTkFrame(govde, fg_color="transparent")
        av_row.pack(fill="x", pady=(4, 8))
        self._avatar_w = AvatarWidget(
            av_row,
            self._hedef_id,
            self._profil.get("avatar_yolu"),
            boyut=88,
            yuvarlak=True,
        )
        self._avatar_w.pack(anchor="w")

        ust_satir = ctk.CTkFrame(govde, fg_color="transparent")
        ust_satir.pack(fill="x", pady=(0, 8))

        ts = self._profil.get("takip_sayilari") or {}
        gi = self._profil.get("gorev_istatistik") or {}
        stats = ctk.CTkFrame(ust_satir, fg_color="transparent")
        stats.pack(side="left", fill="both", expand=True)

        for sayi, etiket in (
            (gi.get("tamamlanan", 0) + gi.get("aktif", 0), "Görev"),
            (ts.get("takipci", 0), "Takipçi"),
            (ts.get("takip_edilen", 0), "Takip"),
        ):
            h = ctk.CTkFrame(stats, fg_color="transparent")
            h.pack(side="left", expand=True)
            ctk.CTkLabel(h, text=str(sayi), font=ctk.CTkFont(size=20, weight="bold")).pack()
            ctk.CTkLabel(h, text=etiket, text_color=COLOR_TEXT_MUTED, font=ctk.CTkFont(size=12)).pack()

        ad = self._profil.get("ad_soyad") or self._profil.get("email")
        ctk.CTkLabel(govde, text=ad, font=ctk.CTkFont(size=15, weight="bold"), anchor="w").pack(
            fill="x", pady=(0, 2)
        )
        if kadi:
            ctk.CTkLabel(govde, text=f"@{kadi}", text_color=COLOR_TEXT_MUTED, anchor="w").pack(fill="x")

        pres = self._feat_repo.presence_getir(self._hedef_id)
        pres_sat = ctk.CTkFrame(govde, fg_color="transparent")
        pres_sat.pack(fill="x", pady=(4, 0))
        online_dot(pres_sat, bool(int(pres.get("cevrimici") or 0))).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(
            pres_sat,
            text=self._feat.presence_metni(self._hedef_id),
            text_color=COLOR_ACCENT if int(pres.get("cevrimici") or 0) else COLOR_TEXT_MUTED,
            font=font_kucuk(),
            anchor="w",
        ).pack(side="left")

        yetenekler = self._feat_repo.yetenekler_listele(self._hedef_id)
        if yetenekler:
            yt = ctk.CTkFrame(govde, fg_color="transparent")
            yt.pack(fill="x", pady=(6, 0))
            for et in yetenekler[:12]:
                ctk.CTkLabel(
                    yt,
                    text=et,
                    fg_color=COLOR_BG_CARD,
                    corner_radius=6,
                    font=ctk.CTkFont(size=11),
                    width=60,
                ).pack(side="left", padx=2, pady=2)

        bio = (self._profil.get("bio") or "").strip()
        if bio:
            ctk.CTkLabel(govde, text=bio, wraplength=520, justify="left", anchor="w").pack(
                fill="x", pady=(10, 0)
            )
        elif self._benim:
            ctk.CTkLabel(
                govde,
                text="Biyografi eklemek için ⚙ Ayarlar'a gidin.",
                text_color=COLOR_TEXT_MUTED,
                anchor="w",
            ).pack(fill="x", pady=(10, 0))

        if not self._benim:
            btn_row = ctk.CTkFrame(govde, fg_color="transparent")
            btn_row.pack(fill="x", pady=(14, 0))
            if self._profil.get("takip_ediyorum"):
                btn_secondary(btn_row, "Takip ediliyor", height=36, command=self._takibi_birak).pack(
                    side="left", fill="x", expand=True, padx=(0, 4)
                )
            else:
                btn_primary(btn_row, "Takip et", height=36, command=self._takip_et).pack(
                    side="left", fill="x", expand=True, padx=(0, 4)
                )
            if self._on_dm:

                def _mesaj() -> None:
                    self._on_dm(self._hedef_id)

                btn_secondary(btn_row, "Mesaj", width=90, height=36, command=_mesaj).pack(side="right")

        self._profil_sekmeleri(govde)

        ctk.CTkLabel(self._scroll, text="").pack(pady=16)
        self._scroll.update_idletasks()

    def _profil_sekmeleri(self, ust_parent: ctk.CTkFrame) -> None:
        wrap = ctk.CTkFrame(self._scroll, fg_color="transparent")
        wrap.pack(fill="x", padx=20, pady=(20, 0))
        tabs = ctk.CTkTabview(wrap, height=360)
        tabs.pack(fill="x")
        t_g = tabs.add("📷 Gönderiler")
        t_h = tabs.add("ℹ Hakkında")
        t_e = tabs.add("👥 Ekipler")
        self._sekme_gonderiler(t_g)
        self._sekme_hakkinda(t_h)
        self._sekme_ekipler(t_e)

    def _sekme_hakkinda(self, parent: ctk.CTkFrame) -> None:
        bio = (self._profil.get("bio") or "").strip() if self._profil else ""
        gi = (self._profil.get("gorev_istatistik") or {}) if self._profil else {}
        metin = bio or "Biyografi eklenmemiş."
        ctk.CTkLabel(parent, text=metin, wraplength=480, justify="left").pack(anchor="w", padx=12, pady=12)
        ctk.CTkLabel(
            parent,
            text=f"Tamamlanan görev: {gi.get('tamamlanan', 0)}  ·  Aktif: {gi.get('aktif', 0)}",
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=12)

    def _sekme_ekipler(self, parent: ctk.CTkFrame) -> None:
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        ekipler = (self._profil.get("ekipler") or []) if self._profil else []
        if not ekipler:
            bos_durum_karti(scroll, "👥", "Ekip yok", "Henüz bir çalışma alanına üye değil.").pack(
                fill="x", pady=12
            )
        else:
            for e in ekipler:
                kart = ctk.CTkFrame(
                    scroll, fg_color=COLOR_BG_CARD, corner_radius=10, border_width=1, border_color=COLOR_BORDER
                )
                kart.pack(fill="x", pady=4)
                ctk.CTkLabel(kart, text=str(e.get("ekip_ad") or "Ekip"), font=ctk.CTkFont(weight="bold")).pack(
                    anchor="w", padx=12, pady=(8, 2)
                )
                ctk.CTkLabel(kart, text=str(e.get("rol_adi") or ""), text_color=COLOR_PRIMARY).pack(
                    anchor="w", padx=12, pady=(0, 8)
                )

    def _sekme_gonderiler(self, parent: ctk.CTkFrame) -> None:
        kutu = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        kutu.pack(fill="both", expand=True)
        try:
            gonderiler = self._social.profil_gonderileri(self._hedef_id, int(self._user["id"]))
        except Exception as ex:
            ctk.CTkLabel(kutu, text=str(ex), text_color=COLOR_TEXT_MUTED).pack(anchor="w", pady=8)
            return
        if not gonderiler:
            bos_durum_karti(
                kutu,
                "📷",
                "Gönderi yok",
                "Henüz paylaşım yapılmamış." if not self._benim else "İlk gönderinizi paylaşın.",
            ).pack(fill="x", pady=12)
            return
        for g in gonderiler:
            self._gonderi_karti(kutu, g)

    def _gonderi_karti(self, parent: ctk.CTkFrame, g: dict[str, Any]) -> None:
        kart = ctk.CTkFrame(
            parent,
            fg_color=COLOR_BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        kart.pack(fill="x", pady=4)
        if g.get("ekip_ad"):
            ctk.CTkLabel(
                kart,
                text=f"📁 {g['ekip_ad']}",
                text_color=COLOR_PRIMARY,
                font=ctk.CTkFont(size=11),
            ).pack(anchor="w", padx=12, pady=(8, 0))
        ctk.CTkLabel(
            kart,
            text=str(g.get("icerik") or ""),
            wraplength=520,
            justify="left",
        ).pack(anchor="w", padx=12, pady=8)
        alt = ctk.CTkFrame(kart, fg_color="transparent")
        alt.pack(fill="x", padx=10, pady=(0, 8))
        gid = int(g["id"])
        begeni = int(g.get("begeni_sayisi") or 0)
        begendim = bool(g.get("begendim"))
        tarih = str(g.get("olusturma_tarihi") or "")[:16]
        ctk.CTkLabel(alt, text=tarih, text_color=COLOR_TEXT_MUTED, font=ctk.CTkFont(size=11)).pack(
            side="left"
        )

        def _begeni(toggle_id: int = gid) -> None:
            self._social.begeni_toggle(toggle_id, int(self._user["id"]))
            self._yenile()

        btn_secondary(alt, f"{'♥' if begendim else '♡'} {begeni}", width=72, height=28, command=_begeni).pack(
            side="right", padx=2
        )

        kayitli = bool(g.get("kayitli"))

        def _kaydet(toggle_id: int = gid) -> None:
            self._feat_repo.gonderi_kaydet_toggle(toggle_id, int(self._user["id"]))
            self._toast_goster("Kaydedildi." if not kayitli else "Kayıttan çıkarıldı.", "info")
            self._yenile()

        btn_secondary(alt, "Kaydet" if not kayitli else "Kayıtlı", width=64, height=28, command=_kaydet).pack(
            side="right", padx=2
        )

        def _paylas() -> None:
            metin = str(g.get("icerik") or "")[:200]
            try:
                root = self.winfo_toplevel()
                root.clipboard_clear()
                root.clipboard_append(metin)
            except Exception:
                pass
            self._toast_goster("Metin panoya kopyalandı (paylaşım).", "info")

        btn_secondary(alt, "Paylaş", width=64, height=28, command=_paylas).pack(side="right", padx=2)

        if self._benim and g.get("gorunurluk"):
            gor = str(g.get("gorunurluk") or "herkes")

            def _gor_degistir(gid=gid, mevcut=gor) -> None:
                import src.config as cfg

                sira = list(cfg.GORUNURLUK_SECENEKLERI)
                try:
                    i = sira.index(mevcut)
                    yeni = sira[(i + 1) % len(sira)]
                except ValueError:
                    yeni = cfg.GORUNURLUK_HERKES
                self._feat_repo.gonderi_gorunurluk_guncelle(gid, yeni)
                self._toast_goster(f"Görünürlük: {yeni}", "info")
                self._yenile()

            btn_secondary(alt, f"Görünür: {gor}", width=100, height=28, command=_gor_degistir).pack(
                side="right", padx=2
            )

    def _takip_et(self) -> None:
        ok, msg = self._svc.takip_et(int(self._user["id"]), self._hedef_id)
        if ok:
            self._toast_goster(msg)
            if self._on_takip_bildirim:
                self._on_takip_bildirim(self._hedef_id, "Yeni takipçi", msg)
            self._yenile()
        else:
            self._toast_goster(msg, "error")

    def _takibi_birak(self) -> None:
        self._svc.takibi_birak(int(self._user["id"]), self._hedef_id)
        self._toast_goster("Takip bırakıldı.", "info")
        self._yenile()
