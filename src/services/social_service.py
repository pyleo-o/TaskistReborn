# -*- coding: utf-8 -*-
"""social_service.py — Davet, katılım isteği ve sosyal feed."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

import src.config as config
from src.repositories.social_repository import SocialRepository
from src.repositories.teams_repository import TeamsRepository
from src.repositories.users_repository import UsersRepository


@dataclass
class IslemSonucu:
    basarili: bool
    mesaj: str
    kayit_id: Optional[int] = None


class SocialService:
    def __init__(
        self,
        social_repo: Optional[SocialRepository] = None,
        teams_repo: Optional[TeamsRepository] = None,
        users_repo: Optional[UsersRepository] = None,
        bildir_fn: Optional[Callable[..., int]] = None,
    ) -> None:
        self._social = social_repo or SocialRepository()
        self._teams = teams_repo or TeamsRepository()
        self._users = users_repo or UsersRepository()
        self._bildir = bildir_fn

    def _kullanici_bul_kimlik(self, kimlik: str) -> Optional[dict[str, Any]]:
        return self._users.kullanici_giris_ile_bul(kimlik)

    def davet_gonder(
        self,
        ekip_id: int,
        davet_eden_id: int,
        hedef_kimlik: str,
        rol_adi: str,
    ) -> IslemSonucu:
        if not self._teams.ekipte_yonetici_mi(int(ekip_id), int(davet_eden_id)):
            return IslemSonucu(False, "Yalnızca ekip yöneticisi davet gönderebilir.")

        hedef = self._kullanici_bul_kimlik(hedef_kimlik)
        if hedef is None:
            return IslemSonucu(False, "Kullanıcı bulunamadı. E-posta veya @kullanici_adi girin.")

        hid = int(hedef["id"])
        if hid == int(davet_eden_id):
            return IslemSonucu(False, "Kendinizi davet edemezsiniz.")

        if self._teams.uyelik_getir(hid, int(ekip_id)):
            return IslemSonucu(False, "Bu kullanıcı zaten ekip üyesi.")

        if self._social.davet_bekleyen_var_mi(int(ekip_id), hid):
            return IslemSonucu(False, "Bu kullanıcıya zaten bekleyen davet var.")

        rid = self._teams.rol_id_rol_adindan((rol_adi or "").strip())
        if rid is None:
            return IslemSonucu(False, "Geçersiz rol.")

        davet_id = self._social.davet_ekle(int(ekip_id), hid, int(davet_eden_id), int(rid))
        ekip_ad = self._teams.uyelik_getir(int(davet_eden_id), int(ekip_id))
        ad = (ekip_ad or {}).get("ekip_ad") or "Ekip"
        kadi = hedef.get("kullanici_adi") or hedef.get("email", "")
        if self._bildir:
            self._bildir(
                hid,
                "Ekip daveti",
                f"«{ad}» ekibine {rol_adi} rolüyle davet edildiniz.",
                tip=config.BILDIRIM_TIP_EKIP_DAVET,
                ekip_id=int(ekip_id),
                ilgili_kullanici_id=int(davet_eden_id),
                ilgili_kayit_id=davet_id,
            )
        return IslemSonucu(True, f"@{kadi} kullanıcısına davet gönderildi.", davet_id)

    def davet_kabul(self, davet_id: int, kullanici_id: int) -> IslemSonucu:
        d = self._social.davet_getir(int(davet_id))
        if d is None or d.get("durum") != config.DAVET_DURUM_BEKLEMEDE:
            return IslemSonucu(False, "Davet bulunamadı veya süresi dolmuş.")
        if int(d["hedef_kullanici_id"]) != int(kullanici_id):
            return IslemSonucu(False, "Bu davet size ait değil.")

        ekip_id = int(d["ekip_id"])
        if self._teams.uyelik_getir(int(kullanici_id), ekip_id):
            self._social.davet_durum_guncelle(int(davet_id), config.DAVET_DURUM_KABUL)
            return IslemSonucu(True, "Zaten üyesiniz.")

        self._teams.ekip_uye_ekle(ekip_id, int(kullanici_id), int(d["rol_id"]))
        self._social.davet_durum_guncelle(int(davet_id), config.DAVET_DURUM_KABUL)

        if self._bildir:
            self._bildir(
                int(d["davet_eden_id"]),
                "Davet kabul edildi",
                f"Bir kullanıcı «{d.get('ekip_ad')}» davetinizi kabul etti.",
                tip=config.BILDIRIM_TIP_DAVET_KABUL,
                ekip_id=ekip_id,
                ilgili_kullanici_id=int(kullanici_id),
                ilgili_kayit_id=int(davet_id),
            )
        return IslemSonucu(True, f"«{d.get('ekip_ad')}» ekibine katıldınız.")

    def davet_reddet(self, davet_id: int, kullanici_id: int) -> IslemSonucu:
        d = self._social.davet_getir(int(davet_id))
        if d is None or int(d.get("hedef_kullanici_id", -1)) != int(kullanici_id):
            return IslemSonucu(False, "Davet bulunamadı.")
        self._social.davet_durum_guncelle(int(davet_id), config.DAVET_DURUM_RED)
        return IslemSonucu(True, "Davet reddedildi.")

    def katilim_istegi_gonder(self, ekip_id: int, kullanici_id: int, mesaj: str = "") -> IslemSonucu:
        if self._teams.uyelik_getir(int(kullanici_id), int(ekip_id)):
            return IslemSonucu(False, "Bu ekibe zaten üyesiniz.")
        if self._social.katilim_bekleyen_var_mi(int(ekip_id), int(kullanici_id)):
            return IslemSonucu(False, "Bekleyen katılma isteğiniz var.")

        istek_id = self._social.katilim_istegi_ekle(int(ekip_id), int(kullanici_id), mesaj)
        yonetici_id = self._social.ekip_olusturan_id(int(ekip_id))
        istek = self._social.katilim_istegi_getir(istek_id)
        if yonetici_id and self._bildir and istek:
            ad = istek.get("ad_soyad") or istek.get("kullanici_adi") or "Bir kullanıcı"
            self._bildir(
                int(yonetici_id),
                "Katılma isteği",
                f"{ad} «{istek.get('ekip_ad')}» ekibine katılmak istiyor.",
                tip=config.BILDIRIM_TIP_KATILIM_ISTEGI,
                ekip_id=int(ekip_id),
                ilgili_kullanici_id=int(kullanici_id),
                ilgili_kayit_id=istek_id,
            )
        return IslemSonucu(True, "Katılma isteğiniz yöneticiye iletildi.", istek_id)

    def katilim_onayla(self, istek_id: int, onaylayan_id: int, rol_adi: str) -> IslemSonucu:
        istek = self._social.katilim_istegi_getir(int(istek_id))
        if istek is None or istek.get("durum") != config.KATILIM_DURUM_BEKLEMEDE:
            return IslemSonucu(False, "İstek bulunamadı.")
        ekip_id = int(istek["ekip_id"])
        if not self._teams.ekipte_yonetici_mi(ekip_id, int(onaylayan_id)):
            return IslemSonucu(False, "Yalnızca yönetici onaylayabilir.")

        uid = int(istek["kullanici_id"])
        if self._teams.uyelik_getir(uid, ekip_id):
            self._social.katilim_durum_guncelle(int(istek_id), config.KATILIM_DURUM_ONAY)
            return IslemSonucu(True, "Kullanıcı zaten üye.")

        rid = self._teams.rol_id_rol_adindan((rol_adi or config.ROL_SISTEM_ANALISTI).strip())
        if rid is None:
            return IslemSonucu(False, "Geçersiz rol.")
        self._teams.ekip_uye_ekle(ekip_id, uid, int(rid))
        self._social.katilim_durum_guncelle(int(istek_id), config.KATILIM_DURUM_ONAY)

        if self._bildir:
            self._bildir(
                uid,
                "Katılım onaylandı",
                f"«{istek.get('ekip_ad')}» ekibine katılımınız onaylandı ({rol_adi}).",
                tip=config.BILDIRIM_TIP_KATILIM_ONAY,
                ekip_id=ekip_id,
                ilgili_kullanici_id=int(onaylayan_id),
                ilgili_kayit_id=int(istek_id),
            )
        return IslemSonucu(True, "Kullanıcı ekibe eklendi.")

    def katilim_reddet(self, istek_id: int, onaylayan_id: int) -> IslemSonucu:
        istek = self._social.katilim_istegi_getir(int(istek_id))
        if istek is None:
            return IslemSonucu(False, "İstek bulunamadı.")
        if not self._teams.ekipte_yonetici_mi(int(istek["ekip_id"]), int(onaylayan_id)):
            return IslemSonucu(False, "Yetkiniz yok.")
        self._social.katilim_durum_guncelle(int(istek_id), config.KATILIM_DURUM_RED)
        return IslemSonucu(True, "İstek reddedildi.")

    def kesfedilebilir_ekipler(self, kullanici_id: int) -> list[dict[str, Any]]:
        return self._social.kesfedilebilir_ekipler(int(kullanici_id))

    def bekleyen_katilim_istekleri(self, ekip_id: int) -> list[dict[str, Any]]:
        return self._social.ekip_bekleyen_katilim_istekleri(int(ekip_id))

    def bekleyen_davetler(self, kullanici_id: int) -> list[dict[str, Any]]:
        return self._social.bekleyen_davetler(int(kullanici_id))

    def feed_listele(self, kullanici_id: int) -> list[dict[str, Any]]:
        return self._social.feed_listele(int(kullanici_id))

    def profil_gonderileri(self, kullanici_id: int, izleyen_id: Optional[int] = None) -> list[dict[str, Any]]:
        return self._social.kullanici_gonderileri(int(kullanici_id), izleyen_id)

    def gonderi_paylas(
        self,
        kullanici_id: int,
        icerik: str,
        ekip_id: Optional[int] = None,
        gorunurluk: str = config.GORUNURLUK_HERKES,
    ) -> IslemSonucu:
        metin = (icerik or "").strip()
        if len(metin) < 1:
            return IslemSonucu(False, "Gönderi metni boş olamaz.")
        if len(metin) > 2000:
            return IslemSonucu(False, "Gönderi en fazla 2000 karakter olabilir.")
        if gorunurluk not in config.GORUNURLUK_SECENEKLERI:
            gorunurluk = config.GORUNURLUK_HERKES
        if ekip_id is not None and self._teams.uyelik_getir(int(kullanici_id), int(ekip_id)) is None:
            return IslemSonucu(False, "Yalnızca üye olduğunuz ekipte paylaşım yapabilirsiniz.")
        gid = self._social.gonderi_ekle(int(kullanici_id), metin, ekip_id, gorunurluk)
        return IslemSonucu(True, "Gönderi paylaşıldı.", gid)

    def begeni_toggle(self, gonderi_id: int, kullanici_id: int) -> bool:
        return self._social.begeni_toggle(int(gonderi_id), int(kullanici_id))
