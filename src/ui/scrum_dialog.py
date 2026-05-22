# -*- coding: utf-8 -*-
"""scrum_dialog.py — Günlük scrum üç soru modalı."""

from __future__ import annotations

from typing import Any, Callable, Optional

import customtkinter as ctk

from src.services.scrum_service import ScrumService


class ScrumDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master: Any,
        kullanici_id: int,
        ekip_id: int,
        ekip_ad: str,
        scrum: ScrumService,
        on_kayit: Callable[[str], None],
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)
        self._uid = int(kullanici_id)
        self._eid = int(ekip_id)
        self._scrum = scrum
        self._on_kayit = on_kayit

        self.title("Günlük Scrum Asistanı")
        self.geometry("520x480")
        self.resizable(False, False)
        try:
            self.transient(master.winfo_toplevel())
        except Exception:
            pass
        self.grab_set()

        frm = ctk.CTkFrame(self, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            frm,
            text=f"{ekip_ad} — Bugünün planı",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", pady=(0, 12))

        self._dun = self._alan(frm, "Dün ne yaptınız?")
        self._bugun = self._alan(frm, "Bugün ne yapacaksınız? *")
        self._engel = self._alan(frm, "Engeliniz var mı?")

        ctk.CTkButton(frm, text="Kaydet", command=self._kaydet).pack(fill="x", pady=(12, 0))

    def _alan(self, parent: ctk.CTkFrame, etiket: str) -> ctk.CTkTextbox:
        ctk.CTkLabel(parent, text=etiket).pack(anchor="w")
        tb = ctk.CTkTextbox(parent, height=70)
        tb.pack(fill="x", pady=(4, 10))
        return tb

    def _kaydet(self) -> None:
        ok, msg = self._scrum.kaydet(
            self._uid,
            self._eid,
            self._dun.get("1.0", "end"),
            self._bugun.get("1.0", "end"),
            self._engel.get("1.0", "end"),
        )
        if not ok:
            self._on_kayit(msg)
            return
        self._on_kayit(msg)
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
