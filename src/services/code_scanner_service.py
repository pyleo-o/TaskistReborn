# -*- coding: utf-8 -*-
"""code_scanner_service.py — Kod tarayıcı (ast + basit kurallar)."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import List


@dataclass
class TaramaSonucu:
    basarili: bool
    hatalar: List[str]
    ozet: str


class CodeScannerService:
    """Python kodu için hafif statik analiz simülasyonu."""

    MAX_SATIR = 200

    def tara(self, kod_metni: str) -> TaramaSonucu:
        kod = (kod_metni or "").strip()
        if not kod:
            return TaramaSonucu(False, ["Kod alanı boş."], "Boş kod.")

        hatalar: list[str] = []

        for i, satir in enumerate(kod.splitlines(), 1):
            if len(satir) > self.MAX_SATIR:
                hatalar.append(f"Satır {i}: Satır çok uzun ({len(satir)} karakter).")
            if re.search(r"\bprint\s*\(", satir) and "debug" not in satir.lower():
                hatalar.append(f"Satır {i}: Üretim kodunda print() kullanımı önerilmez.")
            if "TODO" in satir or "FIXME" in satir:
                hatalar.append(f"Satır {i}: Tamamlanmamış TODO/FIXME işareti.")
            if re.match(r"\s*except\s*:\s*$", satir):
                hatalar.append(f"Satır {i}: Boş except bloğu (Exception belirtilmeli).")

        try:
            tree = ast.parse(kod)
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    hatalar.append(f"Satır {node.lineno}: Geniş except yakalama.")
        except SyntaxError as se:
            hatalar.append(f"Sözdizimi hatası: {se.msg} (satır {se.lineno})")

        if hatalar:
            ozet = "Kod Tarayıcı: " + str(len(hatalar)) + " uyarı/hata bulundu.\n" + "\n".join(
                hatalar[:15]
            )
            return TaramaSonucu(False, hatalar, ozet)

        ozet = (
            "Kod Tarayıcı: Statik kurallar ve AST analizi tamamlandı.\n"
            "Sonuç: Hata bulunamadı. Görev test aşamasına uygun."
        )
        return TaramaSonucu(True, [], ozet)
