# -*- coding: utf-8 -*-
"""app_shell.py — Tek pencere kabuğu ve modern üst menü."""

from __future__ import annotations

from typing import Any, Callable, Literal, Optional

import customtkinter as ctk

import src.config as config
from src.db import init_database
from src.repositories.users_repository import UsersRepository
from src.services.auth_service import AuthService
from src.services.dashboard_service import DashboardService
from src.services.notification_service import NotificationService
from src.services.profile_service import ProfileService
from src.services.scrum_service import ScrumService
from src.services.features_service import FeaturesService
from src.services.social_service import SocialService
from src.ui.dm_panel import dm_cekmecesi_goster
from src.services.workspace_service import WorkspaceService
from src.ui.components.navbar import AppNavbar
from src.ui.dashboard_admin_view import AdminDashboardView
from src.ui.dashboard_dev_view import DeveloperDashboardView
from src.ui.dashboard_tester_view import TesterDashboardView
from src.ui.dialogs import ctk_hata
from src.ui.login_view import LoginView
from src.ui.notifications_panel import bildirim_cekmecesi_goster
from src.ui.profile_view import ProfileView
from src.ui.scrum_dialog import ScrumDialog
from src.ui.teams_view import TeamsView
from src.ui.theme import COLOR_BG_APP, COLOR_BG_CARD, NavSayfa
from src.ui.toast import ToastManager
from src.ui.tooltip import tooltip_kapat_hepsi

ToastTip = Literal["success", "warning", "error", "info"]


class AppShell:
    def __init__(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title(config.UI_APP_TITLE)
        self.root.geometry(config.UI_DEFAULT_GEOMETRY)
        self.root.minsize(config.UI_MIN_WIDTH, config.UI_MIN_HEIGHT)
        self.root.configure(fg_color=COLOR_BG_APP)

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        self._navbar_slot = ctk.CTkFrame(self.root, fg_color=COLOR_BG_CARD, height=56)
        self._navbar_slot.grid(row=0, column=0, sticky="ew")
        self._navbar_slot.grid_propagate(False)
        self._navbar_slot.grid_remove()
        self._navbar: Optional[AppNavbar] = None

        self.container = ctk.CTkFrame(self.root, fg_color=COLOR_BG_APP)
        self.container.grid(row=1, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.toast = ToastManager(self.root)
        self.auth = AuthService()
        self.workspaces = WorkspaceService()
        self.dashboards = DashboardService()
        self.notify = NotificationService()
        self.features = FeaturesService(bildir_fn=self.notify.bildir)
        self.social = SocialService(bildir_fn=self.notify.bildir)
        self.scrum = ScrumService()
        self.profiles = ProfileService()
        self._users = UsersRepository()

        self.current_user: Optional[dict[str, Any]] = None
        self._tema_koyu = True
        self._aktif_ekip_id: Optional[int] = None
        self._aktif_sayfa: NavSayfa = "ana"

        try:
            init_database()
        except Exception as ex:
            ctk_hata(self.root, "Veritabanı", str(ex))
            raise

        self.root.bind("<Control-f>", lambda _e: self._navbar_ara_odak())
        self.root.bind("<Control-h>", lambda _e: self.ekiplerim_goster() if self.current_user else None)
        self.root.bind("<Control-m>", lambda _e: self._dm_ac())
        self.root.bind(
            "<Control-k>",
            lambda _e: self.toast_goster(
                "Kısayollar: Ctrl+H ana sayfa, Ctrl+M mesajlar, Ctrl+F arama, Ctrl+K bu liste.",
                tip="info",
            ),
        )
        self.root.after(8000, self._presence_dongusu)

        self.giris_goster()

    def _presence_dongusu(self) -> None:
        if self.current_user:
            self.features.heartbeat(int(self.current_user["id"]))
        self.root.after(60000, self._presence_dongusu)

    def _dm_ac(self, hedef_id: Optional[int] = None) -> None:
        if not self.current_user:
            return
        self._aktif_sayfa = "mesaj"

        def _kapat() -> None:
            self._aktif_sayfa = "ana"
            self._navbar_goster()

        dm_cekmecesi_goster(
            self.container,
            self.current_user,
            self.features,
            on_kapat=_kapat,
            on_profil=lambda uid: self.profil_goster(hedef_id=uid),
            toast_fn=self.toast_goster,
            hedef_id=hedef_id,
        )

    def toast_goster(self, mesaj: str, tip: ToastTip = "info", baslik: Optional[str] = None) -> None:
        self.toast.goster(mesaj, tip=tip, baslik=baslik)

    def _navbar_goster(self) -> None:
        self._navbar_slot.grid(row=0, column=0, sticky="ew")
        for w in self._navbar_slot.winfo_children():
            w.destroy()
        if not self.current_user:
            return
        n = self.notify.okunmamis(int(self.current_user["id"]))
        self._navbar = AppNavbar(
            self._navbar_slot,
            kullanici=self.current_user,
            okunmamis=n,
            aktif_sayfa=self._aktif_sayfa,
            on_profil=self._profilim,
            on_bildirim=self._bildirim_ac,
            on_dm=self._dm_ac,
            on_ana_sayfa=self.ekiplerim_goster,
            on_ara=self._global_ara,
        )
        self._navbar.pack(fill="x")

    def _navbar_gizle(self) -> None:
        for w in self._navbar_slot.winfo_children():
            w.destroy()
        self._navbar = None
        self._navbar_slot.grid_remove()

    def _kullanici_yenile(self) -> None:
        if not self.current_user:
            return
        from src.ui.components.avatar import AvatarWidget

        AvatarWidget.onbellek_temizle(int(self.current_user["id"]))
        row = self._users.kullanici_id_ile_bul(int(self.current_user["id"]))
        if row:
            full = self._users.kullanici_email_ile_bul(self.current_user["email"])
            if full:
                self.current_user = {
                    "id": int(full["id"]),
                    "email": full["email"],
                    "ad_soyad": full.get("ad_soyad") or "",
                    "kullanici_adi": full.get("kullanici_adi") or "",
                    "avatar_yolu": full.get("avatar_yolu"),
                }
        self._navbar_goster()

    def _tema_degistir(self) -> None:
        self._tema_koyu = not self._tema_koyu
        ctk.set_appearance_mode("dark" if self._tema_koyu else "light")
        self.toast_goster(f"{'Koyu' if self._tema_koyu else 'Açık'} tema", tip="info")

    def _navbar_ara_odak(self) -> None:
        try:
            if self._navbar and hasattr(self._navbar, "_ent_ara"):
                ent = self._navbar._ent_ara
                if ent.winfo_exists():
                    ent.focus_set()
        except Exception:
            pass

    def _global_ara(self, kimlik: str) -> None:
        if not kimlik or not self.current_user:
            self.toast_goster("Arama terimi girin.", tip="info")
            return
        try:
            sonuclar = self.profiles.ara(kimlik)
        except Exception as ex:
            self.toast_goster(str(ex), tip="error")
            return
        if not sonuclar:
            self.toast_goster("Kullanıcı bulunamadı.", tip="warning")
            return
        self.profil_goster(hedef_id=int(sonuclar[0]["id"]))

    def _bildirim_ac(self) -> None:
        if not self.current_user:
            return
        self._aktif_sayfa = "bildirim"

        def _kapat() -> None:
            self._aktif_sayfa = "ana"
            self._navbar_goster()

        bildirim_cekmecesi_goster(
            self.container,
            int(self.current_user["id"]),
            self.notify,
            self.social,
            on_kapat=_kapat,
            on_profil=lambda uid: self.profil_goster(hedef_id=uid),
            on_islem_sonrasi=self._navbar_goster,
            toast_fn=self.toast_goster,
        )

    def _profilim(self) -> None:
        if self.current_user:
            self._aktif_sayfa = "profil"
            self.profil_goster()

    def _icerigi_temizle(self) -> None:
        tooltip_kapat_hepsi()
        try:
            self.root.focus_set()
        except Exception:
            pass
        for w in self.container.winfo_children():
            w.destroy()

    def giris_goster(self) -> None:
        self.current_user = None
        self._aktif_ekip_id = None
        self._navbar_gizle()
        self.root.title(f"{config.UI_APP_TITLE} — Giriş")
        self._icerigi_temizle()
        LoginView(
            self.container,
            auth_service=self.auth,
            on_basarili_giris=self._giris_sonrasi,
            toast_fn=self.toast_goster,
        ).grid(row=0, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

    def _giris_sonrasi(self, kullanici: dict[str, Any]) -> None:
        self.current_user = kullanici
        self.features.heartbeat(int(kullanici["id"]))
        self.toast_goster("Hoş geldiniz!", tip="success")
        self.ekiplerim_goster()

    def ekiplerim_goster(self) -> None:
        if not self.current_user:
            self.giris_goster()
            return
        self._aktif_sayfa = "ana"
        self._kullanici_yenile()
        self.root.title(f"{config.UI_APP_TITLE} — Ana Sayfa")
        self._icerigi_temizle()
        TeamsView(
            self.container,
            kullanici=self.current_user,
            workspace_service=self.workspaces,
            social_service=self.social,
            on_ekip_secildi=self._ekip_secildi,
            on_cikis=self.giris_goster,
            toast_fn=self.toast_goster,
            on_kullanici_ara=self._kullanici_ara_sonuc,
            profile_service=self.profiles,
            on_profil=self._profilim,
            features_service=self.features,
            on_dm=self._dm_ac,
        ).grid(row=0, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self._navbar_goster()

    def profil_goster(self, hedef_id: Optional[int] = None) -> None:
        if not self.current_user:
            return
        if hedef_id is None or int(hedef_id) == int(self.current_user["id"]):
            self._aktif_sayfa = "profil"
        self._icerigi_temizle()
        hid = hedef_id if hedef_id is not None else int(self.current_user["id"])
        self.root.title(f"{config.UI_APP_TITLE} — Profil")
        ProfileView(
            self.container,
            kullanici=self.current_user,
            profile_service=self.profiles,
            on_geri=self._profil_geri,
            hedef_id=hid,
            toast_fn=self.toast_goster,
            on_takip_bildirim=self._takip_bildirimi_gonder,
            on_avatar_degisti=self._kullanici_yenile,
            on_tema=self._tema_degistir,
            on_cikis=self.giris_goster,
            tema_koyu=self._tema_koyu,
            social_service=self.social,
            features_service=self.features,
            on_dm=self._dm_ac,
        ).grid(row=0, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self._navbar_goster()

    def _profil_geri(self) -> None:
        self.ekiplerim_goster()

    def _kullanici_ara_sonuc(self, kullanici_id: int) -> None:
        self.profil_goster(hedef_id=kullanici_id)

    def _takip_bildirimi_gonder(self, hedef_id: int, baslik: str, mesaj: str) -> None:
        self.notify.bildir(int(hedef_id), baslik, mesaj, tip=config.BILDIRIM_TIP_GENEL)

    def _scrum_goster_gerekirse(self, ekip_id: int, ekip_ad: str) -> None:
        if not self.current_user or not self.scrum.bugun_doldurulmali_mi(
            int(self.current_user["id"]), int(ekip_id)
        ):
            return

        def _toast_mesaj(msg: str) -> None:
            tip: ToastTip = "success" if "kaydedildi" in msg.lower() else "warning"
            self.toast_goster(msg, tip=tip)
            if tip == "success":
                self.notify.bildir(
                    int(self.current_user["id"]),
                    "Scrum",
                    msg,
                    tip=config.BILDIRIM_TIP_SCRUM,
                    ekip_id=int(ekip_id),
                )

        ScrumDialog(
            self.root,
            int(self.current_user["id"]),
            int(ekip_id),
            ekip_ad,
            self.scrum,
            on_kayit=_toast_mesaj,
        )

    def _ekip_secildi(self, ekip_id: int, ekip_ad: str, karttan_rol: str) -> None:
        if not self.current_user:
            return
        try:
            uyelik = self.workspaces.ekipte_rolu_al(int(self.current_user["id"]), int(ekip_id))
        except Exception as ex:
            self.toast_goster(str(ex), tip="error")
            return
        if uyelik is None:
            self.toast_goster("Bu ekibe üyeliğiniz yok.", tip="warning")
            return
        self._aktif_ekip_id = int(ekip_id)
        self._aktif_sayfa = "ekip"
        rol_adi = str(uyelik["rol_adi"])
        self._scrum_goster_gerekirse(int(ekip_id), str(uyelik.get("ekip_ad") or ekip_ad))
        tur = self.dashboards.ekran_turu_rolden(rol_adi)
        self.root.title(f"{config.UI_APP_TITLE} — {self.dashboards.ekran_basligi(rol_adi, ekip_ad)}")
        self._icerigi_temizle()
        ortak = dict(
            kullanici=self.current_user,
            ekip_id=int(ekip_id),
            ekip_ad=str(uyelik.get("ekip_ad") or ekip_ad),
            rol_adi=rol_adi,
            on_geri=self.ekiplerim_goster,
            toast_fn=self.toast_goster,
            notify_fn=self._bildir_gonder,
            on_profil=self.profil_goster,
        )
        if tur == DashboardService.EKRAN_YONETICI:
            view: ctk.CTkFrame = AdminDashboardView(
                self.container,
                workspace_service=self.workspaces,
                profile_service=self.profiles,
                scrum_service=self.scrum,
                social_service=self.social,
                on_kullanici_sec=self._kullanici_ara_sonuc,
                **ortak,
            )
        elif tur == DashboardService.EKRAN_TESTER:
            view = TesterDashboardView(self.container, **ortak)
        else:
            view = DeveloperDashboardView(self.container, **ortak)
        view.grid(row=0, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self._navbar_goster()

    def _bildir_gonder(
        self,
        kullanici_id: int,
        baslik: str,
        mesaj: str,
        tip: str = config.BILDIRIM_TIP_GENEL,
        ekip_id: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        if not self.features.bildirim_izinli_mi(int(kullanici_id), tip):
            return
        self.notify.bildir(
            int(kullanici_id), baslik, mesaj, tip=tip, ekip_id=ekip_id, **kwargs
        )
        if self.current_user and int(self.current_user["id"]) == int(kullanici_id):
            self._navbar_goster()

    def calistir(self) -> None:
        self.root.mainloop()
