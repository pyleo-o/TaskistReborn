# -*- coding: utf-8 -*-
"""admin_gorev_detay.py — Görev detay: alt görev, geçmiş, ekler."""

from __future__ import annotations

from tkinter import filedialog
from typing import Any, Callable, Optional

import customtkinter as ctk

from src.repositories.features_repository import FeaturesRepository
from src.services.admin_task_service import AdminTaskService
from src.ui.components.empty_state import bos_durum_karti
from src.ui.dialogs import ctk_hata, ctk_uyari
from src.ui.theme import COLOR_TEXT_MUTED


class GorevDetayPenceresi(ctk.CTkToplevel):
    def __init__(
        self,
        master: ctk.CTk | ctk.CTkFrame,
        servis: AdminTaskService,
        features_repo: FeaturesRepository,
        gorev_id: int,
        gorev_baslik: str,
        kullanici_id: int,
        toast_fn: Optional[Callable[..., None]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)
        self._servis = servis
        self._repo = features_repo
        self._gid = int(gorev_id)
        self._uid = int(kullanici_id)
        self._toast = toast_fn
        self.title(f"Görev #{self._gid} — {gorev_baslik}")
        self.geometry("560x520")
        self.resizable(True, True)
        try:
            kok = master
            while kok is not None and not isinstance(kok, ctk.CTk):
                kok = getattr(kok, "master", None)
            if isinstance(kok, ctk.CTk):
                self.transient(kok)
        except Exception:
            pass
        self.grab_set()

        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=12, pady=12)
        t_alt = tabs.add("Alt görevler")
        t_gec = tabs.add("Geçmiş")
        t_ek = tabs.add("Ekler")

        self._alt_kutu = ctk.CTkScrollableFrame(t_alt, label_text="Alt görevler")
        self._alt_kutu.pack(fill="both", expand=True)
        alt_alt = ctk.CTkFrame(t_alt, fg_color="transparent")
        alt_alt.pack(fill="x", pady=8)
        self._yeni_alt = ctk.CTkEntry(alt_alt, placeholder_text="Yeni alt görev")
        self._yeni_alt.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(alt_alt, text="Ekle", width=80, command=self._alt_ekle).pack(side="right")

        self._gec_kutu = ctk.CTkScrollableFrame(t_gec, label_text="Aktivite")
        self._gec_kutu.pack(fill="both", expand=True)

        self._ek_kutu = ctk.CTkScrollableFrame(t_ek, label_text="Dosya ekleri")
        self._ek_kutu.pack(fill="both", expand=True)
        ctk.CTkButton(t_ek, text="Dosya ekle…", command=self._ek_ekle).pack(pady=8)

        self._yenile()

    def _toast_goster(self, msg: str, tip: str = "info") -> None:
        if self._toast:
            self._toast(msg, tip=tip)

    def _yenile(self) -> None:
        self._alt_yenile()
        self._gec_yenile()
        self._ek_yenile()

    def _alt_yenile(self) -> None:
        for w in self._alt_kutu.winfo_children():
            w.destroy()
        try:
            satirlar = self._servis.alt_gorevleri_getir(self._gid)
        except Exception as ex:
            ctk_hata(self, "Hata", str(ex))
            return
        if not satirlar:
            bos_durum_karti(self._alt_kutu, "✅", "Alt görev yok", "Aşağıdan ekleyin.").pack(fill="x", pady=8)
            return
        for r in satirlar:
            rid = int(r["id"])
            var = ctk.BooleanVar(value=bool(int(r["tamamlandi"])))
            sat = ctk.CTkFrame(self._alt_kutu, fg_color=("gray88", "gray22"))
            sat.pack(fill="x", pady=4)

            def _kaydet(aid=rid, v=var) -> None:
                self._servis.alt_gorev_tamamlandi_kaydet(aid, bool(v.get()))

            ctk.CTkCheckBox(sat, text=str(r["baslik"]), variable=var, command=_kaydet).pack(
                anchor="w", padx=10, pady=8
            )

    def _alt_ekle(self) -> None:
        metin = self._yeni_alt.get().strip()
        if not metin:
            return
        ok, msg = self._servis.alt_gorev_ekle(self._gid, metin)
        if ok:
            self._yeni_alt.delete(0, "end")
            self._alt_yenile()
        else:
            ctk_uyari(self, "Hata", msg)

    def _gec_yenile(self) -> None:
        for w in self._gec_kutu.winfo_children():
            w.destroy()
        for a in self._repo.gorev_aktivite_listele(self._gid):
            sat = ctk.CTkFrame(self._gec_kutu, fg_color=("gray88", "gray22"))
            sat.pack(fill="x", pady=3)
            kim = a.get("ad_soyad") or a.get("kullanici_adi") or "Sistem"
            ctk.CTkLabel(
                sat,
                text=f"[{str(a.get('tarih') or '')[:16]}] {a.get('islem')} — {kim}\n{a.get('detay') or ''}",
                justify="left",
                wraplength=480,
            ).pack(anchor="w", padx=10, pady=6)

    def _ek_yenile(self) -> None:
        for w in self._ek_kutu.winfo_children():
            w.destroy()
        ekler = self._repo.gorev_ekleri_listele(self._gid)
        if not ekler:
            bos_durum_karti(self._ek_kutu, "📎", "Ek yok", "Dosya ekleyebilirsiniz.").pack(fill="x", pady=8)
            return
        for e in ekler:
            ctk.CTkLabel(
                self._ek_kutu,
                text=f"• {e.get('dosya_adi')} ({str(e.get('tarih') or '')[:10]})",
                anchor="w",
            ).pack(fill="x", padx=8, pady=4)

    def _ek_ekle(self) -> None:
        yol = filedialog.askopenfilename(parent=self)
        if not yol:
            return
        import os

        ad = os.path.basename(yol)
        try:
            self._repo.gorev_ek_ekle(self._gid, yol, ad, self._uid)
            self._repo.gorev_aktivite_ekle(
                self._gid, "EK_EKLENDI", ad, kullanici_id=self._uid, ekip_id=self._servis.ekip_id
            )
            self._toast_goster("Dosya eklendi.")
            self._ek_yenile()
            self._gec_yenile()
        except Exception as ex:
            ctk_hata(self, "Ek", str(ex))
