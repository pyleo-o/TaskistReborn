# -*- coding: utf-8 -*-
"""features_service.py — v4 özellik iş kuralları."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional

import src.config as config
from src.repositories.features_repository import FeaturesRepository
from src.repositories.tasks_repository import TasksRepository
from src.repositories.users_repository import UsersRepository

_MENTION_RE = re.compile(r"@([a-zA-Z0-9_]{2,32})")


@dataclass
class IslemSonucu:
    basarili: bool
    mesaj: str
    kayit_id: Optional[int] = None


class FeaturesService:
    def __init__(
        self,
        repo: Optional[FeaturesRepository] = None,
        users: Optional[UsersRepository] = None,
        tasks: Optional[TasksRepository] = None,
        bildir_fn: Optional[Callable[..., int]] = None,
    ) -> None:
        self._repo = repo or FeaturesRepository()
        self._users = users or UsersRepository()
        self._tasks = tasks or TasksRepository()
        self._bildir = bildir_fn

    def heartbeat(self, kullanici_id: int) -> None:
        self._repo.presence_guncelle(int(kullanici_id), True)

    def presence_metni(self, kullanici_id: int) -> str:
        p = self._repo.presence_getir(int(kullanici_id))
        if int(p.get("cevrimici") or 0):
            return "Çevrimiçi"
        sg = p.get("son_gorulme")
        if not sg:
            return "Son görülme bilinmiyor"
        try:
            dt = datetime.fromisoformat(str(sg).replace("Z", ""))
            fark = datetime.now() - dt
            dk = int(fark.total_seconds() // 60)
            if dk < 2:
                return "Az önce görüldü"
            if dk < 60:
                return f"{dk} dk önce"
            sa = dk // 60
            if sa < 24:
                return f"{sa} sa önce"
            return f"{sa // 24} gün önce"
        except Exception:
            return f"Son görülme: {str(sg)[:16]}"

    def bildirim_izinli_mi(self, kullanici_id: int, tip: str) -> bool:
        t = self._repo.bildirim_tercihleri_getir(int(kullanici_id))
        if tip == config.BILDIRIM_TIP_ATAMA:
            return bool(t.get("gorev_atama", 1))
        if tip == config.BILDIRIM_TIP_TEST:
            return bool(t.get("test_guncelleme", 1))
        if tip == config.BILDIRIM_TIP_SCRUM:
            return bool(t.get("scrum", 1))
        if tip in (config.BILDIRIM_TIP_EKIP_DAVET, config.BILDIRIM_TIP_KATILIM_ISTEGI):
            return bool(t.get("sosyal", 1))
        if tip == config.BILDIRIM_TIP_DM:
            return bool(t.get("dm", 1))
        if tip == config.BILDIRIM_TIP_DUYURU:
            return bool(t.get("duyuru", 1))
        return True

    def baglanti_onerileri(self, kullanici_id: int, limit: int = 8) -> list[dict[str, Any]]:
        return self._repo.baglanti_onerileri(int(kullanici_id), int(limit))

    def dm_gonder(self, gonderen_id: int, hedef_id: int, icerik: str) -> IslemSonucu:
        metin = (icerik or "").strip()
        if not metin:
            return IslemSonucu(False, "Mesaj boş olamaz.")
        sid = self._repo.sohbet_bul_veya_olustur(int(gonderen_id), int(hedef_id))
        mid = self._repo.mesaj_gonder(sid, int(gonderen_id), metin)
        if self._bildir and self.bildirim_izinli_mi(int(hedef_id), config.BILDIRIM_TIP_DM):
            g = self._users.kullanici_id_ile_bul(int(gonderen_id))
            ad = (g or {}).get("ad_soyad") or (g or {}).get("kullanici_adi") or "Biri"
            self._bildir(
                int(hedef_id),
                "Yeni mesaj",
                f"{ad}: {metin[:80]}",
                tip=config.BILDIRIM_TIP_DM,
                ilgili_kullanici_id=int(gonderen_id),
                ilgili_kayit_id=mid,
            )
        return IslemSonucu(True, "Mesaj gönderildi.", mid)

    def gorev_durum_tasi(
        self,
        gorev_id: int,
        yeni_durum: str,
        kullanici_id: int,
        ekip_id: int,
    ) -> IslemSonucu:
        izinli = (
            config.DURUM_BEKLEMEDE,
            config.DURUM_KODLANIYOR,
            config.DURUM_TESTTE,
            config.DURUM_REVIZYON,
            config.DURUM_TAMAMLANDI,
            config.DURUM_KOD_INCELEMEDE,
        )
        if yeni_durum not in izinli:
            return IslemSonucu(False, "Geçersiz durum.")
        self._repo.gorev_durum_guncelle(int(gorev_id), yeni_durum)
        self._repo.gorev_aktivite_ekle(
            int(gorev_id),
            "DURUM_DEGISTI",
            f"Yeni durum: {yeni_durum}",
            kullanici_id=int(kullanici_id),
            ekip_id=int(ekip_id),
        )
        return IslemSonucu(True, f"Görev «{yeni_durum}» sütununa taşındı.")

    def mention_isle(self, aciklama: str, ekip_id: int, gorev_id: int, yapan_id: int) -> list[str]:
        """@kullanici adlarını bulur, bildirim gönderir."""
        bulunan: list[str] = []
        for m in _MENTION_RE.findall(aciklama or ""):
            u = self._users.kullanici_kadi_ile_bul(m)
            if u is None:
                continue
            uid = int(u["id"])
            if uid == int(yapan_id):
                continue
            bulunan.append(m)
            self._repo.gorev_aktivite_ekle(
                int(gorev_id),
                "MENTION",
                f"@{m} görevde anıldı",
                kullanici_id=int(yapan_id),
                ekip_id=int(ekip_id),
            )
            if self._bildir and self.bildirim_izinli_mi(uid, config.BILDIRIM_TIP_GENEL):
                self._bildir(
                    uid,
                    "Görevde anıldınız",
                    f"@{m} bir görev açıklamasında geçiyor (görev #{gorev_id}).",
                    tip=config.BILDIRIM_TIP_GENEL,
                    ekip_id=int(ekip_id),
                    ilgili_kayit_id=int(gorev_id),
                )
        return bulunan

    def dashboard_ozet(self, ekip_id: int) -> dict[str, Any]:
        oz = self._repo.ekip_gorev_ozeti(int(ekip_id))
        saglik = self._repo.ekip_saglik_skoru(int(ekip_id))
        sprintler = self._repo.sprintler_listele(int(ekip_id))
        aktif_sprint = next((s for s in sprintler if s.get("durum") == config.SPRINT_DURUM_AKTIF), None)
        return {
            "gorev_ozet": oz,
            "saglik": saglik,
            "aktif_sprint": aktif_sprint,
            "sprint_sayisi": len(sprintler),
            "duyuru_sayisi": len(self._repo.duyurular_listele(int(ekip_id), 5)),
        }
