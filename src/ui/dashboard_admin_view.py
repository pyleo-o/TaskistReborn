# -*- coding: utf-8 -*-
"""
dashboard_admin_view.py — Yönetici paneli (görev oluşturma + görev tahtası).

Raporla uyumlu özellikler:
- Sol: yeni görev formu (başlık, açıklama, son teslim, kritiklik, yazılımcı seçimi).
- Sağ: kaydırılabilir görev listesi; kritiklik 'Kritik' ise kartta belirgin kırmızı vurgu.
- Alt görevler: görev kartındaki detay düğmesi ile açılan pencerede checkbox ve yeni alt görev ekleme.

Veri erişimi AdminTaskService + TasksRepository üzerinden SQLite'a yazılır.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

import customtkinter as ctk

import src.config as config
from src.services.admin_task_service import AdminTaskService
from src.repositories.features_repository import FeaturesRepository
from src.services.analytics_service import AnalyticsService
from src.services.features_service import FeaturesService
from src.services.profile_service import ProfileService
from src.services.scrum_service import ScrumService
from src.services.social_service import SocialService
from src.services.workspace_service import WorkspaceService
from src.ui.admin_gorev_detay import GorevDetayPenceresi
from src.ui.components.empty_state import bos_durum_karti
from src.ui.components.ui_widgets import AccordionSection, saglik_cubugu, yukleniyor_etiket
from src.ui.theme import (
    COLOR_BG_APP,
    COLOR_BG_CARD,
    COLOR_BG_MUTED,
    COLOR_BORDER,
    COLOR_PRIMARY,
    COLOR_DANGER,
    COLOR_TEXT_MUTED,
    DURUM_KOLON_RENK,
    btn_primary,
    btn_secondary,
    font_baslik,
    font_govde,
    label_field,
    surface_card,
)
from src.ui.components.avatar import AvatarWidget
from src.ui.dialogs import ctk_hata, ctk_uyari
from src.ui.tooltip import tooltip_ekle
from src.ui.components.task_card import modern_gorev_karti

# Kritik görev kartları için rubrik vurgusu (koyu temada yüksek kontrast)
_KRITIK_KENARLIK = "#e74c3c"
_KRITIK_BASLIK_RENK = "#ff5b5b"
_VARSAYILAN_KENARLIK = ("gray70", "gray32")


class _AltGorevlerPenceresi(ctk.CTkToplevel):
    """
    Görev detayı: alt görevleri listeler, checkbox ile tamamlandı işaretlenir,
    yeni alt görev metin kutusu + Ekle ile satır eklenir.
    """

    def __init__(
        self,
        master: ctk.CTk | ctk.CTkFrame,
        servis: AdminTaskService,
        gorev_id: int,
        gorev_baslik: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)
        self._servis = servis
        self._gorev_id = int(gorev_id)
        self.title(f"Alt görevler — {gorev_baslik}")
        self.geometry("520x460")
        self.resizable(False, False)
        try:
            kok = master
            while kok is not None and not isinstance(kok, ctk.CTk):
                kok = getattr(kok, "master", None)
            if isinstance(kok, ctk.CTk):
                self.transient(kok)
        except Exception:
            pass
        self.grab_set()

        self._kutu = ctk.CTkScrollableFrame(self, label_text="Alt görevler (işaretle = tamamlandı)")
        self._kutu.pack(fill="both", expand=True, padx=14, pady=(12, 8))

        alt = ctk.CTkFrame(self, fg_color="transparent")
        alt.pack(fill="x", padx=14, pady=(0, 12))

        self._yeni_ent = ctk.CTkEntry(alt, placeholder_text="Yeni alt görev başlığı")
        self._yeni_ent.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(alt, text="Ekle", width=90, command=self._alt_ekle).pack(side="right")

        self._satir_degiskenleri: dict[int, ctk.BooleanVar] = {}
        self._yenile()

    def _yenile(self) -> None:
        """Liste çocuklarını temizleyip veritabanından tekrar yükler."""
        for w in self._kutu.winfo_children():
            w.destroy()
        self._satir_degiskenleri.clear()

        try:
            satirlar = self._servis.alt_gorevleri_getir(self._gorev_id)
        except Exception as ex:
            ctk_hata(self, "Okuma hatası", str(ex))
            return

        if not satirlar:
            ctk.CTkLabel(self._kutu, text="Henüz alt görev yok. Aşağıdan ekleyebilirsiniz.").pack(
                anchor="w", padx=6, pady=6
            )
            return

        for r in satirlar:
            rid = int(r["id"])
            var = ctk.BooleanVar(value=bool(int(r["tamamlandi"])))
            self._satir_degiskenleri[rid] = var

            sat = ctk.CTkFrame(self._kutu, fg_color=("gray88", "gray22"))
            sat.pack(fill="x", padx=4, pady=4)

            def _kaydet(alt_id: int, v: ctk.BooleanVar) -> None:
                try:
                    ok, msg = self._servis.alt_gorev_tamamlandi_kaydet(alt_id, bool(v.get()))
                except Exception as ex:
                    ctk_hata(self, "Kayıt hatası", str(ex))
                    return
                if not ok:
                    ctk_uyari(self, "Güncellenemedi", msg)

            chk = ctk.CTkCheckBox(
                sat,
                text=str(r["baslik"]),
                variable=var,
                command=lambda aid=rid, vv=var: _kaydet(aid, vv),
            )
            chk.pack(anchor="w", padx=10, pady=8)

    def _alt_ekle(self) -> None:
        metin = self._yeni_ent.get().strip()
        if not metin:
            ctk_uyari(self, "Eksik bilgi", "Alt görev başlığı boş olamaz.")
            return
        try:
            ok, msg = self._servis.alt_gorev_ekle(self._gorev_id, metin)
        except Exception as ex:
            ctk_hata(self, "Hata", str(ex))
            return
        if not ok:
            ctk_uyari(self, "Eklenemedi", msg)
            return
        self._yeni_ent.delete(0, "end")
        self._yenile()

    def kapat(self) -> None:
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()


class AdminDashboardView(ctk.CTkFrame):
    """Yönetici paneli: iki sütunlu düzen + görev tahtası."""

    def __init__(
        self,
        master: ctk.CTkFrame,
        kullanici: dict[str, Any],
        ekip_id: int,
        ekip_ad: str,
        rol_adi: str,
        on_geri: Callable[[], None],
        task_service: Optional[AdminTaskService] = None,
        workspace_service: Optional[WorkspaceService] = None,
        profile_service: Optional[ProfileService] = None,
        scrum_service: Optional[ScrumService] = None,
        social_service: Optional[SocialService] = None,
        toast_fn: Optional[Callable[..., None]] = None,
        notify_fn: Optional[Callable[..., None]] = None,
        on_kullanici_sec: Optional[Callable[[int], None]] = None,
        on_profil: Optional[Callable[[int], None]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color=COLOR_BG_APP, **kwargs)
        self._user = kullanici
        self._ekip_id = int(ekip_id)
        self._ekip_ad = ekip_ad
        self._rol_adi = rol_adi
        self._on_geri = on_geri
        self._feat = FeaturesService()
        self._feat_repo = FeaturesRepository()
        self._servis = task_service or AdminTaskService(self._ekip_id, features=self._feat)
        self._ws = workspace_service or WorkspaceService()
        self._profiles = profile_service or ProfileService()
        self._scrum = scrum_service or ScrumService()
        self._social = social_service or SocialService()
        self._analytics = AnalyticsService(self._ekip_id)
        self._kanban_drag: dict[str, Any] = {"gid": None, "kart": None, "kaynak_kolon": None}
        self._kolon_frames: dict[str, ctk.CTkFrame] = {}
        self._kolon_highlight: dict[str, ctk.CTkFrame] = {}
        self._secili_gorev_id: Optional[int] = None
        self._toast = toast_fn
        self._notify = notify_fn
        self._on_kullanici_sec = on_kullanici_sec
        self._secili_gorev: Optional[dict[str, Any]] = None

        # Geliştirici OptionMenu eşlemesi: etiket -> kullanici_id
        self._dev_etiketler: list[str] = []
        self._dev_idleri: list[int] = []

        self._scroll_gorevler: Optional[ctk.CTkScrollableFrame] = None
        self._opt_kritik: Optional[ctk.CTkOptionMenu] = None
        self._opt_dev: Optional[ctk.CTkOptionMenu] = None
        self._ent_baslik: Optional[ctk.CTkEntry] = None
        self._txt_detay: Optional[ctk.CTkTextbox] = None
        self._ent_due: Optional[ctk.CTkEntry] = None
        self._ent_davet_kimlik: Optional[ctk.CTkEntry] = None
        self._opt_davet_rol: Optional[ctk.CTkOptionMenu] = None
        self._scroll_katilim: Optional[ctk.CTkScrollableFrame] = None

        self._build_layout()

    def _build_layout(self) -> None:
        """Üst şerit + iki sütunlu grid."""
        self.grid_columnconfigure(0, weight=0, minsize=430)
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
            text=f"Yönetici Paneli — {self._ekip_ad}",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=(12, 0))

        ctk.CTkLabel(
            ust,
            text=f"Oturum: {self._user.get('email')}  |  Bu ekipteki rolünüz: {self._rol_adi}",
            text_color="gray65",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        sol = surface_card(self, elevated=True)
        sol.grid(row=1, column=0, padx=(14, 8), pady=(0, 14), sticky="nsew")
        self._sol_form(sol)

        sag = surface_card(self, elevated=True)
        sag.grid(row=1, column=1, padx=(8, 14), pady=(0, 14), sticky="nsew")
        sag.grid_rowconfigure(0, weight=1)
        sag.grid_columnconfigure(0, weight=1)

        self._tabs = ctk.CTkTabview(sag)
        self._tabs.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        tab_ozet = self._tabs.add("Özet")
        tab_gorev = self._tabs.add("Görevler")
        tab_duyuru = self._tabs.add("Duyuru")
        tab_sprint = self._tabs.add("Sprint")
        tab_yonetim = self._tabs.add("Yönetim")
        self._yonetim_tabs = ctk.CTkTabview(tab_yonetim)
        self._yonetim_tabs.pack(fill="both", expand=True, padx=4, pady=4)
        tab_scrum = self._yonetim_tabs.add("Scrum")
        tab_denetim = self._yonetim_tabs.add("Denetim")
        tab_rapor = self._yonetim_tabs.add("Performans")
        tab_ara = self._yonetim_tabs.add("Kullanıcı Ara")
        tab_katilim = self._yonetim_tabs.add("Katılma İstekleri")

        self._scroll_ozet = ctk.CTkScrollableFrame(tab_ozet, label_text="Yönetici özeti")
        self._scroll_ozet.pack(fill="both", expand=True)
        ctk.CTkButton(tab_ozet, text="Özeti Yenile", command=self._ozet_yenile).pack(pady=6)

        self._scroll_gorevler = ctk.CTkScrollableFrame(tab_gorev, label_text="Görev tahtası (sürükle-bırak)")
        self._scroll_gorevler.pack(fill="both", expand=True)
        ctk.CTkLabel(
            tab_gorev,
            text="Kartı basılı tutup sütun üzerine bırakarak durum değiştirin.",
            text_color=COLOR_TEXT_MUTED,
            font=ctk.CTkFont(size=11),
        ).pack(anchor="w", padx=12)

        duy_frm = ctk.CTkFrame(tab_duyuru, fg_color="transparent")
        duy_frm.pack(fill="both", expand=True, padx=8, pady=8)
        self._ent_duyuru_baslik = ctk.CTkEntry(duy_frm, placeholder_text="Duyuru başlığı")
        self._ent_duyuru_baslik.pack(fill="x", pady=4)
        self._txt_duyuru = ctk.CTkTextbox(duy_frm, height=80)
        self._txt_duyuru.pack(fill="x", pady=4)
        ctk.CTkButton(duy_frm, text="Duyuru yayınla", command=self._duyuru_yayinla).pack(anchor="e", pady=4)
        self._scroll_duyuru = ctk.CTkScrollableFrame(duy_frm, label_text="Pano")
        self._scroll_duyuru.pack(fill="both", expand=True)

        spr_frm = ctk.CTkFrame(tab_sprint, fg_color="transparent")
        spr_frm.pack(fill="both", expand=True, padx=8, pady=8)
        self._ent_sprint_ad = ctk.CTkEntry(spr_frm, placeholder_text="Sprint adı")
        self._ent_sprint_ad.pack(fill="x", pady=4)
        self._ent_sprint_hedef = ctk.CTkEntry(spr_frm, placeholder_text="Hedef (opsiyonel)")
        self._ent_sprint_hedef.pack(fill="x", pady=4)
        ctk.CTkButton(spr_frm, text="Sprint oluştur", command=self._sprint_olustur).pack(anchor="e", pady=4)
        self._scroll_sprint = ctk.CTkScrollableFrame(spr_frm, label_text="Sprintler")
        self._scroll_sprint.pack(fill="both", expand=True, pady=8)

        self._scroll_scrum = ctk.CTkScrollableFrame(tab_scrum, label_text="Günlük scrum")
        self._scroll_scrum.pack(fill="both", expand=True)
        btn_scrum = ctk.CTkButton(tab_scrum, text="Özeti Yenile", command=self._scrum_yenile)
        btn_scrum.pack(pady=6)
        tooltip_ekle(btn_scrum, "scrum_ozet")

        self._scroll_denetim = ctk.CTkScrollableFrame(tab_denetim, label_text="İşlem geçmişi")
        self._scroll_denetim.pack(fill="both", expand=True)
        ctk.CTkButton(tab_denetim, text="Günlüğü Yenile", command=self._denetim_yenile).pack(pady=6)

        self._scroll_rapor = ctk.CTkScrollableFrame(tab_rapor, label_text="Süre analizi")
        self._scroll_rapor.pack(fill="both", expand=True)
        btn_rapor = ctk.CTkButton(tab_rapor, text="Raporu Yenile", command=self._rapor_yenile)
        btn_rapor.pack(pady=6)
        tooltip_ekle(btn_rapor, "performans_raporu")

        ara_frm = ctk.CTkFrame(tab_ara, fg_color="transparent")
        ara_frm.pack(fill="both", expand=True, padx=8, pady=8)
        self._ent_kullanici_ara = ctk.CTkEntry(ara_frm, placeholder_text="@kullanici veya e-posta")
        self._ent_kullanici_ara.pack(fill="x", pady=6)
        btn_ara = ctk.CTkButton(ara_frm, text="Ara ve Profile Git", command=self._kullanici_ara_tikla)
        btn_ara.pack(fill="x")
        tooltip_ekle(btn_ara, "kullanici_ara")
        self._scroll_ara = ctk.CTkScrollableFrame(ara_frm, label_text="Sonuçlar")
        self._scroll_ara.pack(fill="both", expand=True, pady=8)

        kat_frm = ctk.CTkFrame(tab_katilim, fg_color="transparent")
        kat_frm.pack(fill="both", expand=True, padx=8, pady=8)
        ctk.CTkButton(kat_frm, text="İstekleri Yenile", command=self._katilim_istekleri_yenile).pack(
            anchor="w", pady=6
        )
        self._scroll_katilim = ctk.CTkScrollableFrame(kat_frm, label_text="Bekleyen istekler")
        self._scroll_katilim.pack(fill="both", expand=True)

        self._gelistirici_listesini_doldur()
        self._gorev_listesini_yenile()
        self._ozet_yenile()
        self._duyuru_yenile()
        self._sprint_yenile()
        self._scrum_yenile()
        self._denetim_yenile()
        self._rapor_yenile()
        self._katilim_istekleri_yenile()

    def _sol_form(self, parent: ctk.CTkFrame) -> None:
        """Sol sütun: accordion ile davet + görev formu."""
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent", label_text="")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)
        scroll.grid_columnconfigure(0, weight=1)

        acc_davet = AccordionSection(scroll, "Ekip & davet", acik=False)
        acc_davet.pack(fill="x")
        bd = acc_davet.body
        label_field(bd, "E-posta veya @kullanici").pack(anchor="w", padx=8, pady=(4, 2))
        self._ent_davet_kimlik = ctk.CTkEntry(bd, placeholder_text="@kullanici veya e-posta", height=38)
        self._ent_davet_kimlik.pack(fill="x", padx=8, pady=(0, 6))
        label_field(bd, "Rol").pack(anchor="w", padx=8)
        try:
            roller = self._ws.tum_rol_secenekleri()
        except Exception:
            roller = list(config.VARSAYILAN_ROLLER)
        self._opt_davet_rol = ctk.CTkOptionMenu(bd, values=roller if roller else ["(rol yok)"])
        self._opt_davet_rol.set(roller[0] if roller else "")
        self._opt_davet_rol.pack(fill="x", padx=8, pady=(0, 8))
        btn_davet = btn_primary(bd, "Davet gönder", command=self._davet_tikla)
        btn_davet.pack(fill="x", padx=8, pady=(0, 8))
        tooltip_ekle(btn_davet, "uye_davet")

        acc_gorev = AccordionSection(scroll, "Yeni görev", acik=True)
        acc_gorev.pack(fill="x")
        parent = acc_gorev.body
        parent.grid_columnconfigure(0, weight=1)

        label_field(parent, "Görev başlığı *").pack(anchor="w", padx=8, pady=(4, 2))
        self._ent_baslik = ctk.CTkEntry(parent, placeholder_text="Örn: Ödeme API refaktörü", height=38)
        self._ent_baslik.pack(fill="x", padx=8, pady=(0, 4))

        label_field(parent, "Detay (@kullanici ile anma)").pack(anchor="w", padx=8, pady=(4, 2))
        self._txt_detay = ctk.CTkTextbox(parent, height=88)
        self._txt_detay.pack(fill="x", padx=8, pady=(0, 4))

        label_field(parent, "Şablon").pack(anchor="w", padx=8, pady=(4, 2))
        self._opt_sablon = ctk.CTkOptionMenu(parent, values=["(şablon yok)"])
        self._opt_sablon.pack(fill="x", padx=8, pady=(0, 4))
        btn_secondary(parent, "Şablondan doldur", height=28, command=self._sablondan_doldur).pack(
            fill="x", padx=8, pady=2
        )
        btn_secondary(parent, "Şablon kaydet", height=28, command=self._sablon_kaydet).pack(
            fill="x", padx=8, pady=(0, 6)
        )
        self._sablonlar: list[dict[str, Any]] = []

        label_field(parent, "Son teslim (YYYY-MM-DD)").pack(anchor="w", padx=8, pady=(4, 2))
        self._ent_due = ctk.CTkEntry(parent, placeholder_text="2026-05-20", height=38)
        self._ent_due.pack(fill="x", padx=8, pady=(0, 4))

        label_field(parent, "Kritiklik").pack(anchor="w", padx=8, pady=(4, 2))
        self._opt_kritik = ctk.CTkOptionMenu(parent, values=list(config.KRITIKLIK_SECENEKLERI))
        self._opt_kritik.set(config.ONCELIK_ORTA)
        self._opt_kritik.pack(fill="x", padx=8, pady=(0, 4))

        label_field(parent, "Atanacak yazılımcı *").pack(anchor="w", padx=8, pady=(4, 2))
        self._opt_dev = ctk.CTkOptionMenu(parent, values=["(yükleniyor)"])
        self._opt_dev.pack(fill="x", padx=8, pady=(0, 8))

        btn_gorev = btn_primary(parent, "Görevi Oluştur", height=40, command=self._gorev_olustur_tikla)
        btn_gorev.pack(fill="x", padx=8, pady=(4, 4))
        tooltip_ekle(btn_gorev, "yeni_gorev")
        btn_secondary(parent, "Seçili Görevi Düzenle", command=self._gorev_duzenle_tikla).pack(
            fill="x", padx=8, pady=2
        )
        ctk.CTkButton(
            parent, text="Seçili Görevi Sil", fg_color=COLOR_DANGER, command=self._gorev_sil_tikla, height=36
        ).pack(fill="x", padx=8, pady=(2, 12))
        self._sablonlari_yenile()

    def _davet_tikla(self) -> None:
        """Kullanıcıyı e-posta veya kullanıcı adı ile davet eder (bildirim gider)."""
        assert self._ent_davet_kimlik is not None and self._opt_davet_rol is not None
        kimlik = self._ent_davet_kimlik.get()
        rol = self._opt_davet_rol.get()
        try:
            sonuc = self._social.davet_gonder(
                self._ekip_id,
                int(self._user["id"]),
                kimlik,
                rol,
            )
        except Exception as ex:
            if self._toast:
                self._toast(str(ex), tip="error")
            return
        if self._toast:
            self._toast(sonuc.mesaj, tip="success" if sonuc.basarili else "warning")
        if sonuc.basarili:
            self._ent_davet_kimlik.delete(0, "end")

    def _katilim_istekleri_yenile(self) -> None:
        if not self._scroll_katilim:
            return
        for w in self._scroll_katilim.winfo_children():
            w.destroy()
        try:
            istekler = self._social.bekleyen_katilim_istekleri(self._ekip_id)
        except Exception as ex:
            ctk.CTkLabel(self._scroll_katilim, text=str(ex)).pack()
            return
        if not istekler:
            ctk.CTkLabel(self._scroll_katilim, text="Bekleyen katılma isteği yok.").pack(pady=20)
            return
        for ist in istekler:
            kart = ctk.CTkFrame(self._scroll_katilim, fg_color=("gray92", "gray22"), corner_radius=10)
            kart.pack(fill="x", pady=6)
            ust = ctk.CTkFrame(kart, fg_color="transparent")
            ust.pack(fill="x", padx=10, pady=8)
            uid = int(ist["kullanici_id"])
            AvatarWidget(ust, uid, ist.get("avatar_yolu"), boyut=40, yuvarlak=True).pack(side="left")
            ad = ist.get("ad_soyad") or ist.get("kullanici_adi") or ist.get("email")
            ctk.CTkLabel(ust, text=ad, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=8)
            if ist.get("mesaj"):
                ctk.CTkLabel(kart, text=str(ist["mesaj"])[:200], wraplength=400).pack(anchor="w", padx=12)
            br = ctk.CTkFrame(kart, fg_color="transparent")
            br.pack(fill="x", padx=8, pady=(0, 8))
            iid = int(ist["id"])

            def _profil(hedef=uid) -> None:
                if self._on_kullanici_sec:
                    self._on_kullanici_sec(hedef)

            ctk.CTkButton(br, text="Profil", width=70, command=_profil).pack(side="left", padx=2)

            def _onay(istek_id=iid) -> None:
                s = self._social.katilim_onayla(istek_id, int(self._user["id"]), config.ROL_SISTEM_ANALISTI)
                if self._toast:
                    self._toast(s.mesaj, tip="success" if s.basarili else "warning")
                self._katilim_istekleri_yenile()
                self._gelistirici_listesini_doldur()

            ctk.CTkButton(br, text="Onayla", width=80, fg_color=COLOR_PRIMARY, command=_onay).pack(
                side="left", padx=2
            )

            def _red(istek_id=iid) -> None:
                s = self._social.katilim_reddet(istek_id, int(self._user["id"]))
                if self._toast:
                    self._toast(s.mesaj, tip="info" if s.basarili else "warning")
                self._katilim_istekleri_yenile()

            ctk.CTkButton(br, text="Reddet", width=70, fg_color="transparent", border_width=1, command=_red).pack(
                side="left", padx=2
            )

    def _gelistirici_listesini_doldur(self) -> None:
        """Ekipteki atanabilir geliştiricileri OptionMenu'ye yükler."""
        assert self._opt_dev is not None
        try:
            devler = self._servis.atanabilir_gelistiriciler()
        except Exception as ex:
            ctk_hata(self, "Veritabanı hatası", f"Geliştirici listesi yüklenemedi:\n{ex}")
            self._opt_dev.configure(values=["(liste alınamadı)"])
            self._dev_etiketler = []
            self._dev_idleri = []
            return

        if not devler:
            self._opt_dev.configure(values=["(Bu ekipte atanabilir geliştirici yok)"])
            self._dev_etiketler = []
            self._dev_idleri = []
            return

        etiketler: list[str] = []
        idler: list[int] = []
        for d in devler:
            kid = int(d["kullanici_id"])
            ad = (d.get("ad_soyad") or "").strip()
            ep = str(d.get("email") or "")
            rol = str(d.get("rol_adi") or "")
            etiket = f"{ad or ep} — {rol}"
            etiketler.append(etiket)
            idler.append(kid)

        self._dev_etiketler = etiketler
        self._dev_idleri = idler
        self._opt_dev.configure(values=etiketler)
        self._opt_dev.set(etiketler[0])

    def _secili_gelistirici_id(self) -> Optional[int]:
        """OptionMenu seçiminden kullanici_id çözülür."""
        assert self._opt_dev is not None
        if not self._dev_etiketler:
            return None
        sec = self._opt_dev.get()
        try:
            idx = self._dev_etiketler.index(sec)
        except ValueError:
            return None
        return self._dev_idleri[idx]

    def _gorev_olustur_tikla(self) -> None:
        """Form doğrulama + servis çağrısı + liste yenileme."""
        assert self._ent_baslik is not None and self._txt_detay is not None
        assert self._ent_due is not None and self._opt_kritik is not None

        baslik = self._ent_baslik.get()
        detay = self._txt_detay.get("1.0", "end")
        due = self._ent_due.get()
        kritik = self._opt_kritik.get()

        try:
            atanan = self._secili_gelistirici_id()
        except Exception as ex:
            ctk_hata(self, "Hata", str(ex))
            return

        try:
            sonuc = self._servis.gorev_olustur(
                baslik=baslik,
                aciklama=detay,
                due_date_metni=due,
                kritiklik=kritik,
                atanan_kullanici_id=int(atanan or 0),
                olusturan_kullanici_id=int(self._user["id"]),
            )
        except Exception as ex:
            ctk_hata(self, "Beklenmeyen hata", str(ex))
            return

        if not sonuc.basarili:
            ctk_uyari(self, "Görev oluşturulamadı", sonuc.mesaj)
            return

        if self._toast:
            self._toast(sonuc.mesaj or "Görev atandı.", tip="success")
        if self._notify and sonuc.yeni_gorev_id and atanan:
            import src.config as cfg

            self._notify(
                int(atanan),
                "Yeni görev atandı",
                f"Size yeni görev atandı: {baslik.strip()}",
                tip=cfg.BILDIRIM_TIP_ATAMA,
                ekip_id=self._ekip_id,
            )
        self._ent_baslik.delete(0, "end")
        self._txt_detay.delete("1.0", "end")
        self._ent_due.delete(0, "end")
        self._gorev_listesini_yenile()
        self._denetim_yenile()

    def _gorev_listesini_yenile(self) -> None:
        """Jira/Trello tarzı yatay Kanban panosu."""
        assert self._scroll_gorevler is not None
        for w in self._scroll_gorevler.winfo_children():
            w.destroy()

        try:
            gorevler = self._servis.gorev_kartlari()
        except Exception as ex:
            ctk_hata(self, "Liste hatası", str(ex))
            return

        if not gorevler:
            bos_durum_karti(
                self._scroll_gorevler,
                "📋",
                "Görev tahtası boş",
                "Soldan yeni görev oluşturun veya şablondan başlayın.",
            ).pack(fill="x", padx=20, pady=20)
            return

        kolonlar = [
            config.DURUM_BEKLEMEDE,
            config.DURUM_KODLANIYOR,
            config.DURUM_TESTTE,
            config.DURUM_REVIZYON,
            config.DURUM_TAMAMLANDI,
        ]
        board = ctk.CTkScrollableFrame(
            self._scroll_gorevler,
            orientation="horizontal",
            fg_color=COLOR_BG_APP,
            height=520,
        )
        board.pack(fill="both", expand=True)

        gruplar: dict[str, list] = {k: [] for k in kolonlar}
        for g in gorevler:
            d = str(g.get("durum") or config.DURUM_BEKLEMEDE)
            if d not in gruplar:
                gruplar[config.DURUM_BEKLEMEDE].append(g)
            else:
                gruplar[d].append(g)

        self._kolon_frames.clear()

        self._kolon_highlight.clear()

        for kolon_ad in kolonlar:
            col = ctk.CTkFrame(board, width=280, fg_color=COLOR_BG_MUTED, corner_radius=10)
            col.pack(side="left", fill="y", padx=6, pady=4)
            col.pack_propagate(False)
            self._kolon_frames[kolon_ad] = col
            renk = DURUM_KOLON_RENK.get(kolon_ad, "#6B7280")
            serit = ctk.CTkFrame(col, height=4, fg_color=renk, corner_radius=4)
            serit.pack(fill="x", padx=8, pady=(8, 0))
            serit.pack_propagate(False)
            hl = ctk.CTkFrame(col, height=0, fg_color=COLOR_PRIMARY)
            self._kolon_highlight[kolon_ad] = hl
            bas = ctk.CTkFrame(col, fg_color="transparent")
            bas.pack(fill="x", padx=8, pady=8)
            ctk.CTkLabel(bas, text=kolon_ad, font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
            ctk.CTkLabel(
                bas,
                text=str(len(gruplar[kolon_ad])),
                width=28,
                height=24,
                corner_radius=12,
                fg_color=("#0A66C2", "#1f6aa5"),
                text_color="white",
            ).pack(side="right")
            liste = ctk.CTkScrollableFrame(col, fg_color="transparent", width=260)
            liste.pack(fill="both", expand=True, padx=6, pady=(0, 8))
            for g in gruplar[kolon_ad]:
                kid = int(g["id"])

                def _detay(gg: dict[str, Any] = g, gid: int = kid) -> None:
                    try:
                        win = GorevDetayPenceresi(
                            self.winfo_toplevel(),
                            servis=self._servis,
                            features_repo=self._feat_repo,
                            gorev_id=gid,
                            gorev_baslik=str(gg.get("baslik") or ""),
                            kullanici_id=int(self._user["id"]),
                            toast_fn=self._toast,
                        )
                        win.focus_force()
                    except Exception as ex:
                        ctk_hata(self, "Hata", str(ex))

                def _sec(gg: dict[str, Any] = g) -> None:
                    self._secili_gorev = dict(gg)
                    self._secili_gorev_id = int(gg["id"])
                    self._gorev_listesini_yenile()

                kart = modern_gorev_karti(
                    liste,
                    g,
                    on_sec=_sec,
                    on_detay=_detay,
                    compact=True,
                    secili=(self._secili_gorev_id == kid),
                )
                self._kanban_karta_surukle(kart, kid, kolon_ad)

        board.bind("<ButtonRelease-1>", self._kanban_birak)
        board.bind("<B1-Motion>", self._kanban_surukle_highlight)

    def _kanban_karta_surukle(self, kart: ctk.CTkFrame, gorev_id: int, mevcut_kolon: str) -> None:
        def _basla(_e: Any, gid: int = gorev_id, k: ctk.CTkFrame = kart) -> None:
            self._kanban_drag["gid"] = gid
            self._kanban_drag["kart"] = k
            k.configure(border_width=2, border_color=COLOR_PRIMARY)

        kart.bind("<ButtonPress-1>", _basla)
        kart._mevcut_kolon = mevcut_kolon  # type: ignore[attr-defined]

    def _kanban_surukle_highlight(self, event: Any) -> None:
        if not self._kanban_drag.get("gid"):
            return
        x, y = event.x_root, event.y_root
        for ad, col in self._kolon_frames.items():
            hl = self._kolon_highlight.get(ad)
            if not hl:
                continue
            try:
                x1, y1 = col.winfo_rootx(), col.winfo_rooty()
                x2, y2 = x1 + col.winfo_width(), y1 + col.winfo_height()
                if x1 <= x <= x2 and y1 <= y <= y2:
                    col.configure(border_width=2, border_color=COLOR_PRIMARY)
                else:
                    col.configure(border_width=0)
            except Exception:
                pass

    def _kanban_birak(self, event: Any) -> None:
        for col in self._kolon_frames.values():
            try:
                col.configure(border_width=0)
            except Exception:
                pass
        gid = self._kanban_drag.get("gid")
        kart = self._kanban_drag.get("kart")
        if not gid or not kart:
            return
        self._kanban_drag["gid"] = None
        self._kanban_drag["kart"] = None
        try:
            kart.configure(border_width=1)
        except Exception:
            pass
        hedef_kolon: Optional[str] = None
        x, y = event.x_root, event.y_root
        for ad, col in self._kolon_frames.items():
            try:
                x1, y1 = col.winfo_rootx(), col.winfo_rooty()
                x2, y2 = x1 + col.winfo_width(), y1 + col.winfo_height()
                if x1 <= x <= x2 and y1 <= y <= y2:
                    hedef_kolon = ad
                    break
            except Exception:
                continue
        if not hedef_kolon:
            return
        sonuc = self._feat.gorev_durum_tasi(
            int(gid), hedef_kolon, int(self._user["id"]), self._ekip_id
        )
        if self._toast:
            self._toast(sonuc.mesaj, tip="success" if sonuc.basarili else "warning")
        if sonuc.basarili:
            self._gorev_listesini_yenile()
            self._ozet_yenile()

    def _gorev_duzenle_tikla(self) -> None:
        if not self._secili_gorev:
            ctk_uyari(self, "Seçim", "Önce görev kartında Seç'e tıklayın.")
            return
        assert self._ent_baslik and self._txt_detay and self._ent_due and self._opt_kritik
        ok, msg = self._servis.gorev_guncelle(
            int(self._secili_gorev["id"]),
            self._ent_baslik.get() or str(self._secili_gorev.get("baslik")),
            self._txt_detay.get("1.0", "end"),
            self._ent_due.get() or str(self._secili_gorev.get("due_date") or ""),
            self._opt_kritik.get(),
            yapan_kullanici_id=int(self._user["id"]),
        )
        if ok:
            if self._toast:
                self._toast(msg, tip="success")
            self._gorev_listesini_yenile()
        else:
            ctk_uyari(self, "Hata", msg)

    def _gorev_sil_tikla(self) -> None:
        if not self._secili_gorev:
            ctk_uyari(self, "Seçim", "Önce görev seçin.")
            return
        ok, msg = self._servis.gorev_sil(int(self._secili_gorev["id"]))
        if ok:
            if self._toast:
                self._toast(msg, tip="success")
            self._secili_gorev = None
            self._gorev_listesini_yenile()
        else:
            ctk_uyari(self, "Hata", msg)

    def _scrum_yenile(self) -> None:
        for w in self._scroll_scrum.winfo_children():
            w.destroy()
        try:
            satirlar = self._scrum.ekip_ozeti(self._ekip_id)
        except Exception as ex:
            ctk.CTkLabel(self._scroll_scrum, text=str(ex)).pack(anchor="w")
            return
        if not satirlar:
            ctk.CTkLabel(self._scroll_scrum, text="Bugün scrum kaydı yok.").pack(anchor="w", padx=8)
            return
        for s in satirlar:
            kart = ctk.CTkFrame(self._scroll_scrum, fg_color=("gray88", "gray22"))
            kart.pack(fill="x", padx=4, pady=4)
            metin = (
                f"{s.get('kullanici_gosterim')}\n"
                f"Dün: {s.get('dun_yaptiklarim')}\n"
                f"Bugün: {s.get('bugun_yapacaklarim')}\n"
                f"Engel: {s.get('engel_var_mi')}"
            )
            ctk.CTkLabel(kart, text=metin, justify="left", wraplength=500).pack(anchor="w", padx=10, pady=8)

    def _denetim_yenile(self) -> None:
        for w in self._scroll_denetim.winfo_children():
            w.destroy()
        try:
            loglar = self._servis.denetim_loglari()
        except Exception as ex:
            ctk.CTkLabel(self._scroll_denetim, text=str(ex)).pack(anchor="w")
            return
        for lg in loglar:
            ctk.CTkLabel(
                self._scroll_denetim,
                text=f"[{lg.get('tarih')}] {lg.get('islem_tipi')} — {lg.get('kullanici_gosterim') or '?'}\n{lg.get('detay')}",
                justify="left",
                wraplength=520,
            ).pack(anchor="w", padx=8, pady=4)

    def _rapor_yenile(self) -> None:
        for w in self._scroll_rapor.winfo_children():
            w.destroy()
        try:
            rapor = self._analytics.performans_raporu()
        except Exception as ex:
            ctk.CTkLabel(self._scroll_rapor, text=str(ex)).pack(anchor="w")
            return
        ctk.CTkLabel(
            self._scroll_rapor,
            text=f"Tamamlanan: {rapor['tamamlanan_adet']} | Ortalama süre: {rapor['ortalama_saniye']} sn",
            font=ctk.CTkFont(weight="bold"),
        ).pack(anchor="w", padx=8, pady=8)
        for s in rapor.get("satirlar") or []:
            sn = s.get("sure_saniye")
            ctk.CTkLabel(
                self._scroll_rapor,
                text=f"#{s.get('gorev_id')} {s.get('baslik')} — {s.get('atanan_gosterim')} — {sn or '?'} sn",
                wraplength=520,
            ).pack(anchor="w", padx=12, pady=2)

    def _kullanici_ara_tikla(self) -> None:
        for w in self._scroll_ara.winfo_children():
            w.destroy()
        try:
            sonuclar = self._profiles.ara(self._ent_kullanici_ara.get())
        except Exception as ex:
            ctk_hata(self, "Hata", str(ex))
            return
        for u in sonuclar:
            uid = int(u["id"])
            sat = ctk.CTkFrame(self._scroll_ara, fg_color=("gray88", "gray22"))
            sat.pack(fill="x", pady=4)
            kadi = u.get("kullanici_adi") or u.get("email", "").split("@")[0]
            ctk.CTkLabel(sat, text=f"@{kadi}").pack(side="left", padx=8)

            def _git(hedef=uid) -> None:
                if self._on_kullanici_sec:
                    self._on_kullanici_sec(hedef)

            ctk.CTkButton(sat, text="Profil", width=80, command=_git).pack(side="right", padx=8, pady=4)

    def _ozet_yenile(self) -> None:
        if not hasattr(self, "_scroll_ozet") or not self._scroll_ozet:
            return
        for w in self._scroll_ozet.winfo_children():
            w.destroy()
        try:
            oz = self._feat.dashboard_ozet(self._ekip_id)
        except Exception as ex:
            ctk.CTkLabel(self._scroll_ozet, text=str(ex)).pack(anchor="w", padx=8)
            return
        saglik = oz.get("saglik") or {}
        skor = int(saglik.get("skor") or 0)
        renk = "#2ecc71" if skor >= 70 else "#f39c12" if skor >= 40 else "#e74c3c"
        kart = surface_card(self._scroll_ozet)
        kart.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(kart, text="Ekip sağlık skoru", font=font_baslik(14)).pack(anchor="w", padx=14, pady=(12, 0))
        ctk.CTkLabel(kart, text=f"{skor} / 100", font=font_baslik(32), text_color=renk).pack(
            anchor="w", padx=14, pady=4
        )
        saglik_cubugu(kart, skor)
        ctk.CTkLabel(
            kart,
            text=(
                f"Tamamlanan: {saglik.get('tamamlanan', 0)} / {saglik.get('toplam', 0)}  ·  "
                f"Revize: {saglik.get('revize', 0)}  ·  Açık kritik: {saglik.get('acik_kritik', 0)}"
            ),
            text_color=COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=14, pady=(0, 12))

        gozet = oz.get("gorev_ozet") or {}
        durumlar = gozet.get("durumlar") or {}
        ctk.CTkLabel(
            self._scroll_ozet,
            text=f"Toplam görev: {gozet.get('toplam', 0)}",
            font=ctk.CTkFont(weight="bold"),
        ).pack(anchor="w", padx=12, pady=(8, 4))
        for d, sayi in durumlar.items():
            ctk.CTkLabel(self._scroll_ozet, text=f"  • {d}: {sayi}").pack(anchor="w", padx=16)
        sp = oz.get("aktif_sprint")
        if sp:
            ctk.CTkLabel(
                self._scroll_ozet,
                text=f"Aktif sprint: {sp.get('ad')} ({sp.get('gorev_sayisi', 0)} görev)",
                text_color=COLOR_PRIMARY,
            ).pack(anchor="w", padx=12, pady=8)

    def _duyuru_yayinla(self) -> None:
        baslik = self._ent_duyuru_baslik.get().strip()
        icerik = self._txt_duyuru.get("1.0", "end").strip()
        if not baslik or not icerik:
            if self._toast:
                self._toast("Başlık ve içerik gerekli.", tip="warning")
            return
        did = self._feat_repo.duyuru_ekle(
            self._ekip_id, int(self._user["id"]), baslik, icerik
        )
        if self._toast:
            self._toast("Duyuru yayınlandı.", tip="success")
        self._ent_duyuru_baslik.delete(0, "end")
        self._txt_duyuru.delete("1.0", "end")
        self._duyuru_yenile()

    def _duyuru_yenile(self) -> None:
        if not hasattr(self, "_scroll_duyuru"):
            return
        for w in self._scroll_duyuru.winfo_children():
            w.destroy()
        for d in self._feat_repo.duyurular_listele(self._ekip_id):
            k = ctk.CTkFrame(self._scroll_duyuru, fg_color=("gray88", "gray24"), corner_radius=8)
            k.pack(fill="x", pady=4)
            ctk.CTkLabel(k, text=str(d.get("baslik")), font=ctk.CTkFont(weight="bold")).pack(
                anchor="w", padx=10, pady=(8, 2)
            )
            ctk.CTkLabel(k, text=str(d.get("icerik") or "")[:300], wraplength=420, justify="left").pack(
                anchor="w", padx=10, pady=(0, 8)
            )

    def _sprint_olustur(self) -> None:
        ad = self._ent_sprint_ad.get().strip()
        if not ad:
            return
        self._feat_repo.sprint_ekle(self._ekip_id, ad, self._ent_sprint_hedef.get(), "", "")
        self._ent_sprint_ad.delete(0, "end")
        self._ent_sprint_hedef.delete(0, "end")
        self._sprint_yenile()
        self._ozet_yenile()
        if self._toast:
            self._toast("Sprint oluşturuldu.", tip="success")

    def _sprint_yenile(self) -> None:
        if not hasattr(self, "_scroll_sprint"):
            return
        for w in self._scroll_sprint.winfo_children():
            w.destroy()
        for s in self._feat_repo.sprintler_listele(self._ekip_id):
            k = ctk.CTkFrame(self._scroll_sprint, fg_color=("gray88", "gray24"))
            k.pack(fill="x", pady=4)
            ctk.CTkLabel(
                k,
                text=f"{s.get('ad')} — {s.get('gorev_sayisi', 0)} görev ({s.get('durum')})",
            ).pack(anchor="w", padx=10, pady=8)
            if self._secili_gorev:

                def _ata(sid=int(s["id"])) -> None:
                    if self._secili_gorev:
                        self._feat_repo.gorev_sprint_ata(int(self._secili_gorev["id"]), sid)
                        if self._toast:
                            self._toast("Görev sprinte atandı.", tip="success")

                ctk.CTkButton(k, text="Seçili görevi ata", height=26, command=_ata).pack(
                    anchor="e", padx=8, pady=(0, 8)
                )

    def _sablonlari_yenile(self) -> None:
        if not hasattr(self, "_opt_sablon"):
            return
        self._sablonlar = self._feat_repo.sablonlar_listele(self._ekip_id)
        etiketler = [s.get("baslik", "?") for s in self._sablonlar] or ["(şablon yok)"]
        self._opt_sablon.configure(values=etiketler)
        self._opt_sablon.set(etiketler[0])

    def _sablondan_doldur(self) -> None:
        sec = self._opt_sablon.get()
        for s in self._sablonlar:
            if s.get("baslik") == sec:
                assert self._ent_baslik and self._txt_detay and self._opt_kritik
                self._ent_baslik.delete(0, "end")
                self._ent_baslik.insert(0, str(s.get("baslik") or ""))
                self._txt_detay.delete("1.0", "end")
                self._txt_detay.insert("1.0", str(s.get("aciklama") or ""))
                self._opt_kritik.set(str(s.get("kritiklik") or config.ONCELIK_ORTA))
                if self._toast:
                    self._toast("Şablon yüklendi.", tip="info")
                return

    def _sablon_kaydet(self) -> None:
        assert self._ent_baslik and self._txt_detay and self._opt_kritik
        b = self._ent_baslik.get().strip()
        if not b:
            return
        self._feat_repo.sablon_ekle(
            self._ekip_id,
            b,
            self._txt_detay.get("1.0", "end"),
            self._opt_kritik.get(),
            int(self._user["id"]),
        )
        self._sablonlari_yenile()
        if self._toast:
            self._toast("Şablon kaydedildi.", tip="success")
