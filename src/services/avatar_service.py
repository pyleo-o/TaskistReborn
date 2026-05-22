# -*- coding: utf-8 -*-
"""avatar_service.py — Varsayılan ve kullanıcı profil görselleri."""

from __future__ import annotations

import os
import random
import shutil
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

import src.config as config

_PALETLER = [
    ("#0A66C2", "#FFFFFF"),
    ("#057642", "#FFFFFF"),
    ("#915907", "#FFFFFF"),
    ("#B24020", "#FFFFFF"),
    ("#5F3DC4", "#FFFFFF"),
    ("#E67E22", "#FFFFFF"),
    ("#16A085", "#FFFFFF"),
    ("#C0392B", "#FFFFFF"),
]


class AvatarService:
    def __init__(self) -> None:
        self._defaults_dir = config.AVATAR_DEFAULTS_DIR
        self._user_dir = config.AVATAR_USER_DIR
        os.makedirs(self._defaults_dir, exist_ok=True)
        os.makedirs(self._user_dir, exist_ok=True)
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        for i, (bg, fg) in enumerate(_PALETLER):
            path = os.path.join(self._defaults_dir, f"avatar_{i + 1}.png")
            if os.path.isfile(path):
                continue
            img = Image.new("RGB", (256, 256), bg)
            draw = ImageDraw.Draw(img)
            draw.ellipse((48, 40, 208, 200), fill=fg, outline=bg, width=4)
            draw.ellipse((88, 90, 128, 130), fill=bg)
            draw.ellipse((128, 90, 168, 130), fill=bg)
            draw.arc((90, 120, 166, 190), 20, 160, fill=bg, width=6)
            try:
                font = ImageFont.truetype("segoeui.ttf", 72)
            except Exception:
                font = ImageFont.load_default()
            harf = chr(65 + i)
            draw.text((128, 200), harf, fill=fg, font=font, anchor="mm")
            img.save(path, "PNG")

    def rastgele_varsayilan(self) -> str:
        dosyalar = [f for f in os.listdir(self._defaults_dir) if f.endswith(".png")]
        if not dosyalar:
            self._ensure_defaults()
            dosyalar = [f for f in os.listdir(self._defaults_dir) if f.endswith(".png")]
        sec = random.choice(dosyalar)
        return os.path.join(self._defaults_dir, sec).replace("\\", "/")

    def kullanici_avatar_yolu(self, kullanici_id: int) -> Optional[str]:
        for ext in (".png", ".jpg", ".jpeg", ".webp"):
            p = os.path.join(self._user_dir, f"{kullanici_id}{ext}")
            if os.path.isfile(p):
                return p.replace("\\", "/")
        return None

    def cozumle_yol(self, db_yol: Optional[str], kullanici_id: int) -> Optional[str]:
        ozel = self.kullanici_avatar_yolu(kullanici_id)
        if ozel:
            return ozel
        if db_yol and os.path.isfile(db_yol):
            return db_yol
        return self.rastgele_varsayilan()

    def kayittan_ata(self, kullanici_id: int) -> str:
        src = self.rastgele_varsayilan()
        hedef = os.path.join(self._user_dir, f"{kullanici_id}.png")
        shutil.copy2(src, hedef)
        return hedef.replace("\\", "/")

    def yukle(self, kullanici_id: int, kaynak_dosya: str) -> str:
        for old in os.listdir(self._user_dir):
            if old.startswith(f"{kullanici_id}."):
                try:
                    os.remove(os.path.join(self._user_dir, old))
                except OSError:
                    pass
        hedef = os.path.join(self._user_dir, f"{kullanici_id}.png")
        img = Image.open(kaynak_dosya).convert("RGB")
        img = img.resize((256, 256), Image.Resampling.LANCZOS)
        img.save(hedef, "PNG")
        return hedef.replace("\\", "/")

    def sil(self, kullanici_id: int) -> str:
        for old in os.listdir(self._user_dir):
            if old.startswith(f"{kullanici_id}."):
                try:
                    os.remove(os.path.join(self._user_dir, old))
                except OSError:
                    pass
        return self.rastgele_varsayilan()
