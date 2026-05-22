# -*- coding: utf-8 -*-
"""login_view.py — Tek pencerede giriş ve kayıt."""

from __future__ import annotations

from typing import Any, Callable, Optional

import customtkinter as ctk

from src.services.auth_service import AuthService
from src.ui.theme import COLOR_BG_APP, COLOR_BG_CARD, COLOR_BORDER, COLOR_PRIMARY, COLOR_TEXT_MUTED, btn_primary, font_baslik, font_govde
from src.ui.tooltip import tooltip_ekle


class LoginView(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkFrame,
        auth_service: AuthService,
        on_basarili_giris: Callable[[dict[str, Any]], None],
        toast_fn: Optional[Callable[..., None]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color=COLOR_BG_APP, **kwargs)
        self._auth = auth_service
        self._on_ok = on_basarili_giris
        self._toast = toast_fn
        self._mod = "giris"
        self._form_kutu: Optional[ctk.CTkFrame] = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build()

    def destroy(self, *args: Any, **kwargs: Any) -> None:
        try:
            if hasattr(self, "_g_sifre"):
                self._g_sifre.unbind("<Return>")
        except Exception:
            pass
        super().destroy(*args, **kwargs)

    def _toast_goster(self, mesaj: str, tip: str = "info") -> None:
        if self._toast:
            self._toast(mesaj, tip=tip)

    def _build(self) -> None:
        sol = ctk.CTkFrame(self, fg_color=COLOR_PRIMARY, corner_radius=0)
        sol.grid(row=0, column=0, sticky="nsew")
        ic = ctk.CTkFrame(sol, fg_color="transparent")
        ic.place(relx=0.5, rely=0.5, anchor="center")
        logo = ctk.CTkLabel(ic, text="T", font=ctk.CTkFont(size=48, weight="bold"), text_color="white")
        logo.pack(anchor="w", pady=(0, 8))
        ctk.CTkLabel(ic, text="Taskist Reborn", font=font_baslik(28), text_color="white").pack(
            anchor="w", pady=(0, 12)
        )
        ctk.CTkLabel(
            ic,
            text="Yazılım ekipleri için görev otomasyonu",
            font=ctk.CTkFont(size=15),
            text_color="#E8F4FC",
            wraplength=380,
        ).pack(anchor="w")

        sag = ctk.CTkFrame(self, fg_color=COLOR_BG_APP, corner_radius=0)
        sag.grid(row=0, column=1, sticky="nsew")
        sag.grid_columnconfigure(0, weight=1)
        sag.grid_rowconfigure(0, weight=1)

        kart = ctk.CTkFrame(
            sag,
            fg_color=COLOR_BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        kart.pack(expand=True, fill="both", padx=48, pady=48)
        kart.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(kart, text="Hesabınıza erişin", font=ctk.CTkFont(size=24, weight="bold")).pack(
            anchor="w", padx=32, pady=(28, 16)
        )

        seg_wrap = ctk.CTkFrame(kart, fg_color="transparent")
        seg_wrap.pack(fill="x", padx=32, pady=(0, 16))
        self._seg = ctk.CTkSegmentedButton(
            seg_wrap,
            values=["Giriş Yap", "Kayıt Ol"],
            command=self._sekme_degisti,
            fg_color=("gray85", "gray25"),
            selected_color=COLOR_PRIMARY,
            selected_hover_color="#004182",
            unselected_color=("gray90", "gray30"),
        )
        self._seg.pack(fill="x")
        self._seg.set("Giriş Yap")

        self._form_kutu = ctk.CTkFrame(kart, fg_color="transparent")
        self._form_kutu.pack(fill="both", expand=True, padx=32, pady=(0, 28))
        self._form_giris_goster()

    def _sekme_degisti(self, deger: str) -> None:
        if deger == "Kayıt Ol":
            self._form_kayit_goster()
        else:
            self._form_giris_goster()

    def _form_temizle(self) -> None:
        assert self._form_kutu is not None
        for w in self._form_kutu.winfo_children():
            w.destroy()

    def _form_giris_goster(self) -> None:
        self._mod = "giris"
        self._form_temizle()
        assert self._form_kutu is not None
        k = self._form_kutu

        ctk.CTkLabel(k, text="E-posta veya kullanıcı adı", text_color=COLOR_TEXT_MUTED, anchor="w").pack(
            fill="x", pady=(0, 4)
        )
        self._g_email = ctk.CTkEntry(k, placeholder_text="ornek@sirket.com veya @kullanici", height=44)
        self._g_email.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(k, text="Şifre", text_color=COLOR_TEXT_MUTED, anchor="w").pack(fill="x", pady=(0, 4))
        self._g_sifre = ctk.CTkEntry(k, placeholder_text="••••••••", height=44, show="*")
        self._g_sifre.pack(fill="x", pady=(0, 20))
        self._g_sifre.bind("<Return>", lambda _e: self._giris_dene())

        btn = ctk.CTkButton(
            k,
            text="Giriş Yap",
            height=48,
            fg_color=COLOR_PRIMARY,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._giris_dene,
        )
        btn.pack(fill="x")
        tooltip_ekle(btn, "giris_yap")

        ctk.CTkLabel(
            k,
            text="Hesabınız yok mu? Üstten «Kayıt Ol» sekmesine geçin.",
            text_color=COLOR_TEXT_MUTED,
            font=ctk.CTkFont(size=12),
        ).pack(pady=(16, 0))

    def _form_kayit_goster(self) -> None:
        self._mod = "kayit"
        self._form_temizle()
        assert self._form_kutu is not None
        k = self._form_kutu

        ctk.CTkLabel(
            k,
            text="Ücretsiz hesap oluşturun. Size otomatik bir profil fotoğrafı atanır.",
            text_color=COLOR_TEXT_MUTED,
            wraplength=400,
            justify="left",
        ).pack(anchor="w", pady=(0, 12))

        for lbl, attr, ph, gizli in (
            ("E-posta", "_k_email", "ornek@sirket.com", False),
            ("Kullanıcı adı", "_k_kadi", "kullanici_adi", False),
            ("Ad Soyad", "_k_ad", "Adınız Soyadınız", False),
            ("Şifre (min. 4 karakter)", "_k_sifre", "••••••••", True),
        ):
            ctk.CTkLabel(k, text=lbl, text_color=COLOR_TEXT_MUTED, anchor="w").pack(fill="x", pady=(0, 4))
            ent = ctk.CTkEntry(k, placeholder_text=ph, height=42, show="*" if gizli else "")
            ent.pack(fill="x", pady=(0, 10))
            setattr(self, attr, ent)

        btn = ctk.CTkButton(
            k,
            text="Kayıt Ol",
            height=48,
            fg_color=COLOR_PRIMARY,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._kayit_dene,
        )
        btn.pack(fill="x", pady=(8, 0))
        tooltip_ekle(btn, "kayit_ol")

    def _giris_dene(self) -> None:
        sonuc = self._auth.giris_yap(self._g_email.get(), self._g_sifre.get())
        if not sonuc.basarili or not sonuc.kullanici:
            self._toast_goster(sonuc.mesaj or "Giriş başarısız.", tip="warning")
            return
        kullanici = sonuc.kullanici
        try:
            self._g_sifre.unbind("<Return>")
        except Exception:
            pass
        try:
            self.winfo_toplevel().focus_set()
        except Exception:
            pass
        # Gecikmeli geçiş: CTkEntry'nin ertelenmiş focus_set çağrısı silinmiş widget'a düşmesin
        self.after(50, lambda u=kullanici: self._on_ok(u))

    def _kayit_dene(self) -> None:
        sonuc = self._auth.kayit_ol(
            self._k_email.get(),
            self._k_sifre.get(),
            self._k_ad.get(),
            self._k_kadi.get(),
        )
        if not sonuc.basarili:
            self._toast_goster(sonuc.mesaj, tip="error")
            return
        kayit_email = self._k_email.get().strip()
        self._toast_goster(sonuc.mesaj + " Şimdi giriş yapabilirsiniz.", tip="success")
        self._seg.set("Giriş Yap")
        self._form_giris_goster()
        self._g_email.delete(0, "end")
        self._g_email.insert(0, kayit_email)
