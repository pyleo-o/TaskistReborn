# -*- coding: utf-8 -*-
"""
dashboard_tester_view.py — Tester paneli (onay / revizyon).

Sol: Test aşamasındaki görevler (kritik öncelik kırmızı vurgu).
Sağ: Kod özeti, Onayla (Tamamlandı + süre logu) veya Revize İste (matris + Revizyon).
"""

from __future__ import annotations

from typing import Any, Callable, Optional

import customtkinter as ctk

import src.config as config
from src.services.tester_task_service import TesterTaskService
from src.ui.dialogs import ctk_hata, ctk_uyari
from src.ui.tooltip import tooltip_ekle
from src.ui.ui_utils import kart_kenarligi

_KRITIK_KENAR = "#e74c3c"
_KRITIK_BASLIK = "#ff5b5b"
_VARSAYILAN_KENAR = ("gray70", "gray32")


class TesterDashboardView(ctk.CTkFrame):
    """İki sütunlu tester çalışma alanı."""

    def __init__(
        self,
        master: ctk.CTkFrame,
        kullanici: dict[str, Any],
        ekip_id: int,
        ekip_ad: str,
        rol_adi: str,
        on_geri: Callable[[], None],
        task_service: Optional[TesterTaskService] = None,
        toast_fn: Optional[Callable[..., None]] = None,
        notify_fn: Optional[Callable[..., None]] = None,
        on_profil: Optional[Callable[[int], None]] = None,
        **kwargs: Any,
    ) -> None:
        from src.ui.theme import COLOR_BG_APP

        super().__init__(master, fg_color=COLOR_BG_APP, **kwargs)
        self._user = kullanici
        self._ekip_id = int(ekip_id)
        self._ekip_ad = ekip_ad
        self._rol_adi = rol_adi
        self._on_geri = on_geri
        self._servis = task_service or TesterTaskService(self._ekip_id)
        self._toast = toast_fn
        self._notify = notify_fn
        self._secili: Optional[dict[str, Any]] = None

        self._scroll_sol: Optional[ctk.CTkScrollableFrame] = None
        self._lbl_ozet: Optional[ctk.CTkLabel] = None
        self._opt_matris: Optional[ctk.CTkOptionMenu] = None

        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1, minsize=360)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ust = ctk.CTkFrame(self, fg_color="transparent")
        ust.grid(row=0, column=0, columnspan=2, sticky="ew", padx=14, pady=(14, 8))
        ust.grid_columnconfigure(1, weight=1)

        btn_geri = ctk.CTkButton(ust, text="← Ekiplerime dön", width=160, command=self._on_geri)
        btn_geri.grid(row=0, column=0, sticky="w")
        tooltip_ekle(btn_geri, "geri_ekipler")
        ctk.CTkLabel(
            ust,
            text=f"Tester — {self._ekip_ad}",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=(12, 0))
        ctk.CTkLabel(
            ust,
            text=f"{self._user.get('email')}  |  Rol: {self._rol_adi}",
            text_color="gray65",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        sol = ctk.CTkFrame(self, corner_radius=12, fg_color=("gray92", "gray18"))
        sol.grid(row=1, column=0, padx=(14, 8), pady=(0, 14), sticky="nsew")
        sol.grid_rowconfigure(1, weight=1)
        sol.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(sol, text="Testteki görevler", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, padx=12, pady=(12, 6), sticky="w"
        )
        self._scroll_sol = ctk.CTkScrollableFrame(sol, label_text="")
        self._scroll_sol.grid(row=1, column=0, padx=8, pady=6, sticky="nsew")

        sag = ctk.CTkFrame(self, corner_radius=12, fg_color=("gray92", "gray18"))
        sag.grid(row=1, column=1, padx=(8, 14), pady=(0, 14), sticky="nsew")
        sag.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(sag, text="İnceleme ve karar", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, padx=12, pady=(12, 6), sticky="w"
        )
        self._lbl_ozet = ctk.CTkLabel(
            sag,
            text="Soldan görev seçin.",
            wraplength=540,
            justify="left",
        )
        self._lbl_ozet.grid(row=1, column=0, padx=12, pady=6, sticky="nw")

        ctk.CTkLabel(sag, text="Revizyon kritiklik matrisi").grid(row=2, column=0, padx=12, sticky="w")
        self._opt_matris = ctk.CTkOptionMenu(sag, values=list(config.KRITIKLIK_SECENEKLERI))
        self._opt_matris.set(config.ONCELIK_ORTA)
        self._opt_matris.grid(row=3, column=0, padx=12, pady=(0, 10), sticky="ew")

        btn_onay = ctk.CTkButton(
            sag,
            text="Onayla (Tamamlandı)",
            height=40,
            fg_color="#1e8449",
            hover_color="#196f3d",
            command=self._onay_tikla,
        )
        btn_onay.grid(row=4, column=0, padx=12, pady=4, sticky="ew")
        tooltip_ekle(btn_onay, "onayla")

        btn_rev = ctk.CTkButton(
            sag,
            text="Revize İste (Yazılımcıya iade)",
            height=40,
            fg_color="#922b21",
            hover_color="#78281f",
            command=self._revize_tikla,
        )
        btn_rev.grid(row=5, column=0, padx=12, pady=(4, 14), sticky="ew")
        tooltip_ekle(btn_rev, "revize")

        self._liste_yenile()

    def _kritik_mi(self, r: dict[str, Any]) -> bool:
        return str(r.get("kritiklik") or "") == config.ONCELIK_KRITIK

    def _liste_yenile(self) -> None:
        assert self._scroll_sol is not None
        for w in self._scroll_sol.winfo_children():
            w.destroy()
        self._secili = None
        self._sag_temizle()

        try:
            rows = self._servis.testteki_gorevler()
        except Exception as ex:
            ctk_hata(self, "Liste hatası", str(ex))
            return

        if not rows:
            ctk.CTkLabel(
                self._scroll_sol,
                text="Test aşamasında bekleyen görev yok.",
                wraplength=340,
                justify="left",
            ).pack(anchor="w", padx=8, pady=10)
            return

        for r in rows:
            self._kart_ekle(r)

    def _kart_ekle(self, r: dict[str, Any]) -> None:
        assert self._scroll_sol is not None
        gid = int(r["id"])
        kirmizi = self._kritik_mi(r)

        kart = ctk.CTkFrame(
            self._scroll_sol,
            corner_radius=10,
            border_width=2 if kirmizi else 1,
            border_color=_KRITIK_KENAR if kirmizi else _VARSAYILAN_KENAR,
        )
        kart.pack(fill="x", padx=4, pady=5)

        ctk.CTkLabel(
            kart,
            text=f"#{gid} — {r.get('baslik')}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=_KRITIK_BASLIK if kirmizi else None,
        ).pack(anchor="w", padx=10, pady=(8, 2))

        meta = f"Atanan: {r.get('atanan_gosterim') or '—'}  |  Öncelik: {r.get('kritiklik')}"
        ctk.CTkLabel(kart, text=meta, font=ctk.CTkFont(size=12), text_color="gray68").pack(
            anchor="w", padx=10, pady=(0, 6)
        )

        def _sec() -> None:
            self._secili = dict(r)
            self._sag_doldur(r)

        ctk.CTkButton(kart, text="Seç", width=100, command=_sec).pack(anchor="e", padx=10, pady=(0, 8))

    def _sag_temizle(self) -> None:
        assert self._lbl_ozet is not None
        self._lbl_ozet.configure(text="Soldan görev seçin.")

    def _sag_doldur(self, r: dict[str, Any]) -> None:
        assert self._lbl_ozet is not None
        kod = (r.get("kod_metni") or "(henüz kod yok)").strip()
        oz = (r.get("son_tarama_ozeti") or "(tarama özeti yok)").strip()
        metin = (
            f"Görev: {r.get('baslik')}\n"
            f"Öncelik: {r.get('kritiklik')}\n"
            f"Yazılımcı: {r.get('atanan_gosterim')}\n\n"
            f"--- Kod ---\n{kod[:3500]}{'…' if len(kod) > 3500 else ''}\n\n"
            f"--- Tarayıcı özeti ---\n{oz}"
        )
        self._lbl_ozet.configure(text=metin)

    def _onay_tikla(self) -> None:
        if not self._secili:
            ctk_uyari(self, "Seçim yok", "Önce soldan bir görev seçin.")
            return
        gid = int(self._secili["id"])
        try:
            ok, msg, sure = self._servis.gorev_onayla(gid, int(self._user["id"]))
        except Exception as ex:
            ctk_hata(self, "Hata", str(ex))
            return
        if not ok:
            ctk_uyari(self, "Onaylanamadı", msg)
            return
        if self._toast:
            self._toast(f"{msg} Süre: {sure} sn.", tip="success")
        atanan = self._secili.get("atanan_kullanici_id")
        if self._notify and atanan:
            import src.config as cfg

            self._notify(
                int(atanan),
                "Görev onaylandı",
                f"Görev #{gid} tamamlandı.",
                tip=cfg.BILDIRIM_TIP_TEST,
                ekip_id=self._ekip_id,
            )
        self._liste_yenile()

    def _revize_tikla(self) -> None:
        if not self._secili:
            ctk_uyari(self, "Seçim yok", "Önce soldan bir görev seçin.")
            return
        assert self._opt_matris is not None
        gid = int(self._secili["id"])
        sev = self._opt_matris.get()
        try:
            ok, msg = self._servis.gorev_revize_iste(gid, int(self._user["id"]), sev)
        except Exception as ex:
            ctk_hata(self, "Hata", str(ex))
            return
        if not ok:
            ctk_uyari(self, "Revizyon gönderilemedi", msg)
            return
        if self._toast:
            self._toast(msg, tip="warning")
        atanan = self._secili.get("atanan_kullanici_id")
        if self._notify and atanan:
            import src.config as cfg

            self._notify(
                int(atanan),
                "Revizyon istendi",
                msg,
                tip=cfg.BILDIRIM_TIP_TEST,
                ekip_id=self._ekip_id,
            )
        self._liste_yenile()
