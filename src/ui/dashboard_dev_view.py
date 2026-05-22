# -*- coding: utf-8 -*-
"""dashboard_dev_view.py — Geliştirici paneli."""

from __future__ import annotations

from typing import Any, Callable, Optional

import customtkinter as ctk

import src.config as config
from src.services.developer_task_service import DeveloperTaskService
from src.ui.dialogs import ctk_hata, ctk_uyari
from src.ui.tooltip import tooltip_ekle
from src.ui.ui_utils import due_date_gecikmis_mi, kart_kenarligi


class DeveloperDashboardView(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkFrame,
        kullanici: dict[str, Any],
        ekip_id: int,
        ekip_ad: str,
        rol_adi: str,
        on_geri: Callable[[], None],
        task_service: Optional[DeveloperTaskService] = None,
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
        self._servis = task_service or DeveloperTaskService(self._ekip_id)
        self._toast = toast_fn
        self._notify = notify_fn
        self._secili: Optional[dict[str, Any]] = None
        self._scroll_sol: Optional[ctk.CTkScrollableFrame] = None
        self._lbl_detay: Optional[ctk.CTkLabel] = None
        self._txt_kod: Optional[ctk.CTkTextbox] = None
        self._txt_tarama: Optional[ctk.CTkTextbox] = None
        self._build()

    def _toast_goster(self, msg: str, tip: str = "success") -> None:
        if self._toast:
            self._toast(msg, tip=tip)

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1, minsize=360)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ust = ctk.CTkFrame(self, fg_color="transparent")
        ust.grid(row=0, column=0, columnspan=2, sticky="ew", padx=14, pady=(14, 8))
        btn_geri = ctk.CTkButton(ust, text="← Ekiplerime dön", width=160, command=self._on_geri)
        btn_geri.grid(row=0, column=0, sticky="w")
        tooltip_ekle(btn_geri, "geri_ekipler")
        ctk.CTkLabel(ust, text=f"Geliştirici — {self._ekip_ad}", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=1, sticky="w", padx=12
        )

        sol = ctk.CTkFrame(self, corner_radius=12, fg_color=("gray92", "gray18"))
        sol.grid(row=1, column=0, padx=(14, 8), pady=(0, 14), sticky="nsew")
        sol.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(sol, text="Görevlerim", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, padx=12, pady=12, sticky="w"
        )
        self._scroll_sol = ctk.CTkScrollableFrame(sol, label_text="")
        self._scroll_sol.grid(row=1, column=0, padx=8, pady=6, sticky="nsew")

        sag = ctk.CTkFrame(self, corner_radius=12, fg_color=("gray92", "gray18"))
        sag.grid(row=1, column=1, padx=(8, 14), pady=(0, 14), sticky="nsew")
        sag.grid_columnconfigure(0, weight=1)
        sag.grid_rowconfigure(3, weight=1)

        self._lbl_detay = ctk.CTkLabel(sag, text="Soldan görev seçin.", wraplength=520, justify="left")
        self._lbl_detay.grid(row=0, column=0, padx=12, pady=12, sticky="nw")

        btn_ustlen = ctk.CTkButton(sag, text="Görevi Üstlen", command=self._ustlen_tikla)
        btn_ustlen.grid(row=1, column=0, padx=12, pady=4, sticky="ew")
        tooltip_ekle(btn_ustlen, "gorev_ustlen")

        self._txt_kod = ctk.CTkTextbox(sag, height=140)
        self._txt_kod.grid(row=2, column=0, padx=12, pady=8, sticky="nsew")
        self._txt_kod.insert("1.0", "# Kodunuzu buraya yazın...\n")

        self._txt_tarama = ctk.CTkTextbox(sag, height=100, state="disabled")
        self._txt_tarama.grid(row=3, column=0, padx=12, pady=4, sticky="nsew")

        btn_kod = ctk.CTkButton(sag, text="Kodu Yükle / Test İste", command=self._kod_gonder_tikla)
        btn_kod.grid(row=4, column=0, padx=12, pady=4, sticky="ew")
        tooltip_ekle(btn_kod, "kod_yukle")

        btn_zorla = ctk.CTkButton(
            sag, text="Yine de Teste Gönder", fg_color="gray35", command=self._teste_zorla_tikla
        )
        btn_zorla.grid(row=5, column=0, padx=12, pady=(4, 12), sticky="ew")
        tooltip_ekle(btn_zorla, "teste_zorla")

        self._liste_yenile()

    def _liste_yenile(self) -> None:
        assert self._scroll_sol is not None
        for w in self._scroll_sol.winfo_children():
            w.destroy()
        self._secili = None
        try:
            rows = self._servis.bana_atanan_acik_gorevler(int(self._user["id"]))
        except Exception as ex:
            ctk_hata(self, "Liste hatası", str(ex))
            return
        if not rows:
            ctk.CTkLabel(self._scroll_sol, text="Açık görev yok.").pack(anchor="w", padx=8, pady=8)
            return
        for r in rows:
            self._kart_ekle(r)

    def _kart_ekle(self, r: dict[str, Any]) -> None:
        assert self._scroll_sol is not None
        gid = int(r["id"])
        bw, bc = kart_kenarligi(
            str(r.get("kritiklik") or ""),
            str(r.get("durum") or ""),
            r.get("due_date"),
            r.get("revize_kritikligi"),
        )
        gecikme = due_date_gecikmis_mi(r.get("due_date"))
        kart = ctk.CTkFrame(self._scroll_sol, corner_radius=10, border_width=bw, border_color=bc)
        kart.pack(fill="x", padx=4, pady=5)
        bas = f"#{gid} — {r.get('baslik')}"
        if gecikme:
            bas += " [GECİKMİŞ]"
        ctk.CTkLabel(kart, text=bas, font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=10, pady=(8, 2)
        )
        ctk.CTkLabel(
            kart, text=f"Durum: {r.get('durum')} | Öncelik: {r.get('kritiklik')}", text_color="gray68"
        ).pack(anchor="w", padx=10, pady=(0, 6))

        def _sec() -> None:
            self._secili = dict(r)
            assert self._lbl_detay is not None
            self._lbl_detay.configure(
                text=f"{r.get('baslik')}\nDurum: {r.get('durum')}\n{(r.get('aciklama') or '')[:400]}"
            )

        ctk.CTkButton(kart, text="Seç", width=80, command=_sec).pack(anchor="e", padx=10, pady=(0, 8))

    def _ustlen_tikla(self) -> None:
        if not self._secili:
            ctk_uyari(self, "Seçim", "Önce görev seçin.")
            return
        ok, msg = self._servis.gorev_ustlen(int(self._secili["id"]), int(self._user["id"]))
        if ok:
            self._toast_goster(msg, "success")
            self._liste_yenile()
        else:
            ctk_uyari(self, "Üstlenilemedi", msg)

    def _kod_gonder_tikla(self, zorla: bool = False) -> None:
        if not self._secili or not self._txt_kod:
            ctk_uyari(self, "Seçim", "Önce görev seçin.")
            return
        kod = self._txt_kod.get("1.0", "end").strip()
        gid = int(self._secili["id"])
        try:
            ok, msg, teste = self._servis.kod_yukle_ve_teste_gonder(
                gid, int(self._user["id"]), kod, zorla_test=zorla
            )
        except Exception as ex:
            ctk_hata(self, "Hata", str(ex))
            return
        if self._txt_tarama:
            self._txt_tarama.configure(state="normal")
            self._txt_tarama.delete("1.0", "end")
            self._txt_tarama.insert("1.0", msg)
            self._txt_tarama.configure(state="disabled")
        if ok and teste:
            self._toast_goster("Kod test aşamasına gönderildi.", "success")
            if self._notify and self._secili.get("atanan_kullanici_id"):
                pass
            self._liste_yenile()
        else:
            self._toast_goster("Tarayıcı uyarıları — görev revizyonda.", "warning")

    def _teste_zorla_tikla(self) -> None:
        self._kod_gonder_tikla(zorla=True)
