# -*- coding: utf-8 -*-
"""profile_settings_panel.py — Ortalanmış hesap ayarları (Instagram tarzı)."""

from __future__ import annotations

from tkinter import filedialog
from typing import Any, Callable, Optional

import customtkinter as ctk

from src.repositories.features_repository import FeaturesRepository
from src.services.features_service import FeaturesService
from src.services.profile_service import ProfileService
from src.ui.components.avatar import AvatarWidget
from src.ui.theme import (
    COLOR_BG_APP,
    COLOR_BG_CARD,
    COLOR_BG_MUTED,
    COLOR_BORDER,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_TEXT_MUTED,
)

_PANEL_GENISLIK = 640


class ProfileSettingsPanel(ctk.CTkFrame):
    """Ortada açılan ayarlar kartı."""

    def __init__(
        self,
        master: Any,
        kullanici: dict[str, Any],
        profil: dict[str, Any],
        profile_service: ProfileService,
        tema_koyu: bool,
        on_kapat: Callable[[], None],
        on_tema: Callable[[], None],
        on_cikis: Callable[[], None],
        on_kaydedildi: Callable[[], None],
        toast_fn: Optional[Callable[..., None]] = None,
        features_service: Optional[FeaturesService] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            master,
            fg_color=COLOR_BG_CARD,
            corner_radius=16,
            border_width=1,
            border_color=COLOR_BORDER,
            width=_PANEL_GENISLIK,
            **kwargs,
        )
        self.pack_propagate(False)
        self._user = kullanici
        self._profil = profil
        self._svc = profile_service
        self._uid = int(kullanici["id"])
        self._tema_koyu = tema_koyu
        self._on_kapat = on_kapat
        self._on_tema = on_tema
        self._on_cikis = on_cikis
        self._on_kaydedildi = on_kaydedildi
        self._toast = toast_fn
        self._feat = features_service or FeaturesService()
        self._feat_repo = FeaturesRepository()
        self._avatar_onizleme: Optional[AvatarWidget] = None
        self._build()

    def _toast_goster(self, msg: str, tip: str = "success") -> None:
        if self._toast:
            self._toast(msg, tip=tip)

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # —— Üst çubuk ——
        ust = ctk.CTkFrame(self, fg_color="transparent", height=72)
        ust.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))
        ust.grid_columnconfigure(1, weight=1)
        ust.pack_propagate(False)

        ctk.CTkButton(
            ust,
            text="← Geri",
            width=88,
            height=36,
            fg_color="transparent",
            text_color=COLOR_PRIMARY,
            hover_color=("gray90", "gray28"),
            command=self._on_kapat,
        ).grid(row=0, column=0, sticky="w")

        baslik_wrap = ctk.CTkFrame(ust, fg_color="transparent")
        baslik_wrap.grid(row=0, column=1, padx=16)
        ctk.CTkLabel(
            baslik_wrap,
            text="Hesap ayarları",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            baslik_wrap,
            text=self._user.get("email", ""),
            text_color=COLOR_TEXT_MUTED,
            font=ctk.CTkFont(size=13),
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(
            ust,
            text="✕",
            width=40,
            height=40,
            corner_radius=20,
            fg_color=("gray90", "gray28"),
            hover_color=("gray80", "gray35"),
            command=self._on_kapat,
        ).grid(row=0, column=2, sticky="e")

        ayir = ctk.CTkFrame(self, height=1, fg_color=COLOR_BORDER)
        ayir.grid(row=0, column=0, sticky="ew", padx=24, pady=(72, 0))

        govde = ctk.CTkFrame(self, fg_color="transparent")
        govde.grid(row=1, column=0, sticky="nsew", padx=8, pady=(8, 20))
        govde.grid_columnconfigure(1, weight=1)
        govde.grid_rowconfigure(0, weight=1)

        from src.ui.theme import COLOR_BG_MUTED

        menu = ctk.CTkFrame(govde, fg_color=COLOR_BG_MUTED, width=160, corner_radius=10)
        menu.grid(row=0, column=0, sticky="ns", padx=(8, 4), pady=4)
        menu.grid_propagate(False)

        self._icerik_alan = ctk.CTkScrollableFrame(govde, fg_color="transparent", label_text="")
        self._icerik_alan.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=4)
        self._icerik_alan.grid_columnconfigure(0, weight=1)

        self._menu_bolum = "hesap"
        for anahtar, etiket in (
            ("hesap", "Hesap"),
            ("guvenlik", "Güvenlik"),
            ("bildirim", "Bildirimler"),
            ("yetenek", "Yetenekler"),
            ("gorunum", "Görünüm"),
            ("oturum", "Oturum"),
        ):
            b = ctk.CTkButton(
                menu,
                text=etiket,
                anchor="w",
                fg_color="transparent",
                command=lambda k=anahtar: self._menu_sec(k),
            )
            b.pack(fill="x", padx=6, pady=2)

        self._menu_icerik_goster("hesap")

    def _menu_sec(self, anahtar: str) -> None:
        self._menu_bolum = anahtar
        self._menu_icerik_goster(anahtar)

    def _menu_icerik_goster(self, anahtar: str) -> None:
        for w in self._icerik_alan.winfo_children():
            w.destroy()
        if anahtar == "hesap":
            self._bolum_foto(self._icerik_alan)
            self._bolum_hesap(self._icerik_alan)
        elif anahtar == "guvenlik":
            self._bolum_guvenlik(self._icerik_alan)
        elif anahtar == "bildirim":
            self._bolum_bildirim(self._icerik_alan)
        elif anahtar == "yetenek":
            self._bolum_yetenek(self._icerik_alan)
        elif anahtar == "gorunum":
            self._bolum_gorunum(self._icerik_alan)
        elif anahtar == "oturum":
            self._bolum_oturum(self._icerik_alan)

    def _bolum_bildirim(self, parent: ctk.CTkScrollableFrame) -> None:
        self._bolum_baslik(parent, "Bildirim tercihleri", "Hangi bildirimleri almak istediğinizi seçin.")
        kart = self._kart(parent)
        ic = ctk.CTkFrame(kart, fg_color="transparent")
        ic.pack(fill="x", padx=24, pady=24)
        t = self._feat_repo.bildirim_tercihleri_getir(self._uid)
        self._sw_bildirim: dict[str, ctk.CTkSwitch] = {}
        for anahtar, etiket in (
            ("gorev_atama", "Görev atamaları"),
            ("test_guncelleme", "Test güncellemeleri"),
            ("scrum", "Scrum hatırlatıcı"),
            ("sosyal", "Sosyal (davet, takip)"),
            ("dm", "Doğrudan mesajlar"),
            ("duyuru", "Ekip duyuruları"),
        ):
            sat = ctk.CTkFrame(ic, fg_color="transparent")
            sat.pack(fill="x", pady=4)
            ctk.CTkLabel(sat, text=etiket).pack(side="left")
            sw = ctk.CTkSwitch(sat, text="")
            if int(t.get(anahtar, 1)):
                sw.select()
            sw.pack(side="right")
            self._sw_bildirim[anahtar] = sw
        ctk.CTkButton(ic, text="Tercihleri kaydet", command=self._bildirim_kaydet).pack(fill="x", pady=(12, 0))

    def _bildirim_kaydet(self) -> None:
        tercih = {k: 1 if bool(sw.get()) else 0 for k, sw in self._sw_bildirim.items()}
        self._feat_repo.bildirim_tercihleri_kaydet(self._uid, tercih)
        self._toast_goster("Bildirim tercihleri kaydedildi.")

    def _bolum_yetenek(self, parent: ctk.CTkScrollableFrame) -> None:
        self._bolum_baslik(parent, "Yetenek etiketleri", "Profilinizde görünecek beceriler.")
        kart = self._kart(parent)
        ic = ctk.CTkFrame(kart, fg_color="transparent")
        ic.pack(fill="x", padx=24, pady=24)
        self._yetenek_kutu = ctk.CTkFrame(ic, fg_color="transparent")
        self._yetenek_kutu.pack(fill="x", pady=(0, 8))
        self._ent_yetenek = ctk.CTkEntry(ic, placeholder_text="Örn: Python, React, SQL")
        self._ent_yetenek.pack(fill="x", pady=(0, 8))
        ctk.CTkButton(ic, text="Etiket ekle", command=self._yetenek_ekle).pack(fill="x")
        self._yetenek_listesi_yenile()

    def _yetenek_listesi_yenile(self) -> None:
        for w in self._yetenek_kutu.winfo_children():
            w.destroy()
        for et in self._feat_repo.yetenekler_listele(self._uid):
            sat = ctk.CTkFrame(self._yetenek_kutu, fg_color="transparent")
            sat.pack(fill="x", pady=2)
            ctk.CTkLabel(sat, text=et).pack(side="left")

            def _sil(e=et) -> None:
                self._feat_repo.yetenek_sil(self._uid, e)
                self._yetenek_listesi_yenile()

            ctk.CTkButton(sat, text="✕", width=32, height=24, fg_color="transparent", command=_sil).pack(
                side="right"
            )

    def _yetenek_ekle(self) -> None:
        et = self._ent_yetenek.get().strip()
        if not et:
            return
        self._feat_repo.yetenek_ekle(self._uid, et)
        self._ent_yetenek.delete(0, "end")
        self._yetenek_listesi_yenile()
        self._on_kaydedildi()
        self._toast_goster("Yetenek eklendi.")

    def _bolum_baslik(self, parent: ctk.CTkFrame, baslik: str, aciklama: str = "") -> None:
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(fill="x", padx=16, pady=(24, 10))
        ctk.CTkLabel(wrap, text=baslik, font=ctk.CTkFont(size=16, weight="bold"), anchor="w").pack(
            fill="x"
        )
        if aciklama:
            ctk.CTkLabel(
                wrap,
                text=aciklama,
                text_color=COLOR_TEXT_MUTED,
                font=ctk.CTkFont(size=12),
                anchor="w",
                wraplength=_PANEL_GENISLIK - 80,
            ).pack(fill="x", pady=(4, 0))

    def _kart(self, parent: ctk.CTkFrame) -> ctk.CTkFrame:
        k = ctk.CTkFrame(
            parent,
            fg_color=COLOR_BG_MUTED,
            corner_radius=12,
            border_width=0,
        )
        k.pack(fill="x", padx=16, pady=(0, 8))
        return k

    def _satir_etiket(self, parent: ctk.CTkFrame, etiket: str) -> None:
        ctk.CTkLabel(
            parent,
            text=etiket,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 6))

    def _bolum_foto(self, parent: ctk.CTkScrollableFrame) -> None:
        self._bolum_baslik(
            parent,
            "Profil fotoğrafı",
            "Profilinizde ve gönderilerinizde görünür.",
        )
        kart = self._kart(parent)
        satir = ctk.CTkFrame(kart, fg_color="transparent")
        satir.pack(fill="x", padx=24, pady=24)

        sol = ctk.CTkFrame(satir, fg_color="transparent", width=140)
        sol.pack(side="left")
        sol.pack_propagate(False)
        self._avatar_onizleme = AvatarWidget(
            sol,
            self._uid,
            self._profil.get("avatar_yolu"),
            boyut=112,
            yuvarlak=True,
        )
        self._avatar_onizleme.pack(expand=True)

        sag = ctk.CTkFrame(satir, fg_color="transparent")
        sag.pack(side="left", fill="both", expand=True, padx=(24, 0))
        ctk.CTkLabel(
            sag,
            text="JPG veya PNG yükleyin. Kare görseller en iyi sonucu verir.",
            text_color=COLOR_TEXT_MUTED,
            wraplength=280,
            justify="left",
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", pady=(8, 16))
        ctk.CTkButton(
            sag,
            text="Yeni fotoğraf yükle",
            height=42,
            fg_color=COLOR_PRIMARY,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._foto_degistir,
        ).pack(fill="x", pady=(0, 8))
        ctk.CTkButton(
            sag,
            text="Varsayılan avatar",
            height=38,
            fg_color="transparent",
            border_width=1,
            border_color=COLOR_BORDER,
            command=self._foto_kaldir,
        ).pack(fill="x")

    def _bolum_hesap(self, parent: ctk.CTkScrollableFrame) -> None:
        self._bolum_baslik(
            parent,
            "Kişisel bilgiler",
            "Ad, kullanıcı adı ve biyografinizi düzenleyin.",
        )
        kart = self._kart(parent)
        ic = ctk.CTkFrame(kart, fg_color="transparent")
        ic.pack(fill="x", padx=24, pady=24)

        bio = (self._profil.get("bio") or "").strip()
        for etiket, ph, attr, val in (
            ("Ad Soyad", "Adınız ve soyadınız", "_ent_ad", str(self._profil.get("ad_soyad") or "")),
            ("Kullanıcı adı", "benzersiz_kullanici", "_ent_kadi", str(self._profil.get("kullanici_adi") or "")),
        ):
            self._satir_etiket(ic, etiket)
            ent = ctk.CTkEntry(ic, placeholder_text=ph, height=44, corner_radius=8)
            ent.insert(0, val)
            ent.pack(fill="x", pady=(0, 16))
            setattr(self, attr, ent)

        self._satir_etiket(ic, "Biyografi")
        self._txt_bio = ctk.CTkTextbox(ic, height=100, corner_radius=8)
        self._txt_bio.insert("1.0", bio)
        self._txt_bio.pack(fill="x", pady=(0, 16))

        gizli_sat = ctk.CTkFrame(ic, fg_color="transparent")
        gizli_sat.pack(fill="x", pady=(0, 20))
        sol_g = ctk.CTkFrame(gizli_sat, fg_color="transparent")
        sol_g.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(sol_g, text="Gizli profil", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(
            sol_g,
            text="Açıkken yalnızca siz tam profili görürsünüz.",
            text_color=COLOR_TEXT_MUTED,
            font=ctk.CTkFont(size=11),
            wraplength=360,
        ).pack(anchor="w")
        self._sw_gizli = ctk.CTkSwitch(gizli_sat, text="")
        if int(self._profil.get("profil_gizli") or 0):
            self._sw_gizli.select()
        self._sw_gizli.pack(side="right")

        ctk.CTkButton(
            ic,
            text="Değişiklikleri kaydet",
            height=48,
            fg_color=COLOR_PRIMARY,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._hesap_kaydet,
        ).pack(fill="x")

    def _bolum_guvenlik(self, parent: ctk.CTkScrollableFrame) -> None:
        self._bolum_baslik(parent, "Güvenlik", "Şifrenizi güncelleyin.")
        kart = self._kart(parent)
        ic = ctk.CTkFrame(kart, fg_color="transparent")
        ic.pack(fill="x", padx=24, pady=24)

        self._satir_etiket(ic, "Mevcut şifre")
        self._ent_eski = ctk.CTkEntry(ic, placeholder_text="••••••••", show="*", height=44, corner_radius=8)
        self._ent_eski.pack(fill="x", pady=(0, 16))

        self._satir_etiket(ic, "Yeni şifre")
        self._ent_yeni = ctk.CTkEntry(ic, placeholder_text="En az 4 karakter", show="*", height=44, corner_radius=8)
        self._ent_yeni.pack(fill="x", pady=(0, 20))

        ctk.CTkButton(
            ic,
            text="Şifreyi güncelle",
            height=44,
            fg_color=COLOR_PRIMARY,
            command=self._sifre_kaydet,
        ).pack(fill="x")

    def _bolum_gorunum(self, parent: ctk.CTkScrollableFrame) -> None:
        self._bolum_baslik(parent, "Görünüm", "Arayüz temasını seçin.")
        kart = self._kart(parent)
        ic = ctk.CTkFrame(kart, fg_color="transparent")
        ic.pack(fill="x", padx=24, pady=24)

        self._seg_tema = ctk.CTkSegmentedButton(
            ic,
            values=["Koyu tema", "Açık tema"],
            command=self._tema_secildi,
            selected_color=COLOR_PRIMARY,
            selected_hover_color="#004182",
            height=40,
        )
        self._seg_tema.pack(fill="x")
        self._seg_tema.set("Koyu tema" if self._tema_koyu else "Açık tema")

    def _bolum_oturum(self, parent: ctk.CTkScrollableFrame) -> None:
        self._bolum_baslik(parent, "Oturum", "Hesap oturumu ve çıkış.")
        kart = self._kart(parent)
        ic = ctk.CTkFrame(kart, fg_color="transparent")
        ic.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            ic,
            text=f"E-posta: {self._user.get('email', '')}",
            text_color=COLOR_TEXT_MUTED,
            font=ctk.CTkFont(size=13),
            anchor="w",
            justify="left",
        ).pack(anchor="w", fill="x", padx=4, pady=(0, 16))

        ctk.CTkButton(
            ic,
            text="Çıkış yap",
            height=48,
            fg_color=("gray95", "gray22"),
            border_width=1,
            border_color=COLOR_DANGER,
            text_color=COLOR_DANGER,
            hover_color=("#FFE8E6", "#3D1F1C"),
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._cikis_tikla,
        ).pack(fill="x")

    def _avatar_yenile_onizleme(self) -> None:
        if self._avatar_onizleme:
            row = self._svc.profil_getir(self._uid, self._uid)
            yol = row.get("avatar_yolu") if row else None
            self._avatar_onizleme.yenile(yol)

    def _foto_degistir(self) -> None:
        yol = filedialog.askopenfilename(
            title="Profil fotoğrafı seçin",
            filetypes=[("Görsel", "*.png *.jpg *.jpeg *.webp"), ("Tümü", "*.*")],
        )
        if not yol:
            return
        ok, msg = self._svc.avatar_yukle(self._uid, yol)
        if ok:
            self._toast_goster(msg)
            self._avatar_yenile_onizleme()
            self._on_kaydedildi()
        else:
            self._toast_goster(msg, "error")

    def _foto_kaldir(self) -> None:
        ok, msg = self._svc.avatar_sil(self._uid)
        if ok:
            self._toast_goster(msg, "info")
            self._avatar_yenile_onizleme()
            self._on_kaydedildi()
        else:
            self._toast_goster(msg, "error")

    def _hesap_kaydet(self) -> None:
        ok, msg = self._svc.profil_kaydet(
            self._uid,
            self._ent_ad.get(),
            self._txt_bio.get("1.0", "end"),
            self._ent_kadi.get(),
            bool(self._sw_gizli.get()),
        )
        if ok:
            self._toast_goster(msg)
            self._on_kaydedildi()
        else:
            self._toast_goster(msg, "error")

    def _sifre_kaydet(self) -> None:
        ok, msg = self._svc.sifre_degistir(self._uid, self._ent_eski.get(), self._ent_yeni.get())
        if ok:
            self._toast_goster(msg)
            self._ent_eski.delete(0, "end")
            self._ent_yeni.delete(0, "end")
        else:
            self._toast_goster(msg, "error")

    def _tema_secildi(self, deger: str) -> None:
        koyu_istenen = deger.startswith("Koyu")
        if koyu_istenen != self._tema_koyu:
            self._on_tema()
            self._tema_koyu = koyu_istenen

    def _cikis_tikla(self) -> None:
        self._on_kapat()
        self._on_cikis()


def profil_ayarlari_goster(
    host: ctk.CTkFrame,
    kullanici: dict[str, Any],
    profil: dict[str, Any],
    profile_service: ProfileService,
    tema_koyu: bool,
    on_tema: Callable[[], None],
    on_cikis: Callable[[], None],
    on_guncellendi: Callable[[], None],
    toast_fn: Optional[Callable[..., None]] = None,
    features_service: Optional[FeaturesService] = None,
) -> None:
    """Ortalanmış ayarlar kartı + karartılmış arka plan."""
    for w in host.winfo_children():
        if getattr(w, "_taskist_ayar_overlay", False):
            w.destroy()

    from src.ui.theme import COLOR_OVERLAY_SCRIM

    overlay = ctk.CTkFrame(host, fg_color=COLOR_OVERLAY_SCRIM)
    overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
    overlay._taskist_ayar_overlay = True  # type: ignore[attr-defined]
    overlay.bind("<Button-1>", lambda e: _ayar_kapat(overlay) if e.widget == overlay else None)
    overlay.lift()

    def _kapat() -> None:
        _ayar_kapat(overlay)

    panel = ProfileSettingsPanel(
        overlay,
        kullanici=kullanici,
        profil=profil,
        profile_service=profile_service,
        tema_koyu=tema_koyu,
        on_kapat=_kapat,
        on_tema=on_tema,
        on_cikis=on_cikis,
        on_kaydedildi=on_guncellendi,
        toast_fn=toast_fn,
        features_service=features_service,
    )
    panel.place(relx=0.5, rely=0.5, anchor="center", relheight=0.88)
    panel.lift()

    def _boyut_ayarla(_evt: Any = None) -> None:
        try:
            overlay.update_idletasks()
            h = int(overlay.winfo_height() * 0.88)
            panel.configure(height=max(h, 480))
        except Exception:
            pass

    overlay.after(50, _boyut_ayarla)


def _ayar_kapat(overlay: ctk.CTkFrame) -> None:
    try:
        overlay.destroy()
    except Exception:
        pass
