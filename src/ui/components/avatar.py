# -*- coding: utf-8 -*-
"""avatar.py — Profil görseli bileşeni (önbellek dosya zamanı ile)."""

from __future__ import annotations

import os
from typing import Any, Optional

import customtkinter as ctk
from PIL import Image, ImageDraw

from src.services.avatar_service import AvatarService


class AvatarWidget(ctk.CTkFrame):
    """Yuvarlak görünümlü profil fotoğrafı."""

    _cache: dict[str, ctk.CTkImage] = {}

    def __init__(
        self,
        master: Any,
        kullanici_id: int,
        avatar_yolu: Optional[str] = None,
        boyut: int = 96,
        yuvarlak: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, width=boyut, height=boyut, fg_color="transparent", **kwargs)
        self._uid = int(kullanici_id)
        self._boyut = boyut
        self._yuvarlak = yuvarlak
        self._svc = AvatarService()
        self._img_label = ctk.CTkLabel(self, text="", width=boyut, height=boyut)
        self._img_label.pack()
        yol = self._svc.cozumle_yol(avatar_yolu, self._uid)
        self._yukle(yol)

    @classmethod
    def onbellek_temizle(cls, kullanici_id: Optional[int] = None) -> None:
        """Avatar önbelleğini temizle (fotoğraf değişiminden sonra)."""
        if kullanici_id is None:
            cls._cache.clear()
            return
        uid = str(int(kullanici_id))
        silinecek = [k for k in cls._cache if f"/{uid}." in k.replace("\\", "/") or f"\\{uid}." in k]
        for k in silinecek:
            cls._cache.pop(k, None)

    def _cache_anahtari(self, yol: str) -> str:
        try:
            mtime = int(os.path.getmtime(yol))
        except OSError:
            mtime = 0
        return f"{yol}_{self._boyut}_{mtime}"

    def _yuvarlak_kes(self, img: Image.Image) -> Image.Image:
        img = img.resize((self._boyut, self._boyut), Image.Resampling.LANCZOS)
        if not self._yuvarlak:
            return img
        mask = Image.new("L", (self._boyut, self._boyut), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, self._boyut, self._boyut), fill=255)
        cikti = Image.new("RGBA", (self._boyut, self._boyut))
        cikti.paste(img, (0, 0))
        cikti.putalpha(mask)
        return cikti

    def _yukle(self, yol: Optional[str]) -> None:
        if not yol or not os.path.isfile(yol):
            self._img_label.configure(image=None, text="?", font=ctk.CTkFont(size=self._boyut // 2))
            return

        anahtar = self._cache_anahtari(yol)
        if anahtar not in self._cache:
            ham = Image.open(yol).convert("RGB")
            islenmis = self._yuvarlak_kes(ham)
            self._cache[anahtar] = ctk.CTkImage(
                light_image=islenmis,
                dark_image=islenmis,
                size=(self._boyut, self._boyut),
            )
        self._img_label.configure(image=self._cache[anahtar], text="")

    def yenile(self, avatar_yolu: Optional[str] = None) -> None:
        """Güncel dosyadan yeniden yükle."""
        AvatarWidget.onbellek_temizle(self._uid)
        yol = self._svc.cozumle_yol(avatar_yolu, self._uid)
        self._yukle(yol)
