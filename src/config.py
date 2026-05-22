# -*- coding: utf-8 -*-
"""
config.py — Uygulama sabitleri ve dosya yolları.

Bu dosya, veritabanı yolu ve iş kurallarında tekrar eden metin sabitlerini
tek merkezde toplar. Böylece şema (db/schema.py) ile servis katmanı aynı
dilimleri (durum adları, öncelik seviyeleri) tutarlı kullanır.

Sunum notu: Rol artık kullanıcıda değil; her ekip için Ekip_Uyeleri satırında
tutulur (Jira/Trello benzeri çalışma alanı mantığı).
"""

from __future__ import annotations

import os

# --- Dosya yolları ---
# Proje kökü: TaskistReborn/ (bu dosya: TaskistReborn/src/config.py)
_PROJE_KOKU = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VERITABANI_DOSYASI_ADI = "taskist_reborn.db"
VERITABANI_YOLU = os.path.join(_PROJE_KOKU, VERITABANI_DOSYASI_ADI)

# --- Roller (Roller tablosuna seed edilecek; rapor + sizin 5 rol listesi) ---
ROL_YONETICI = "Yönetici"
ROL_BACKEND = "Backend Geliştirici"
ROL_FRONTEND = "Frontend Geliştirici"
ROL_TESTER = "Tester"
ROL_SISTEM_ANALISTI = "Sistem Analisti"

VARSAYILAN_ROLLER: tuple[str, ...] = (
    ROL_YONETICI,
    ROL_BACKEND,
    ROL_FRONTEND,
    ROL_TESTER,
    ROL_SISTEM_ANALISTI,
)

# --- Görev önceliği (yönetici / tester matrisi ile uyumlu) ---
ONCELIK_KRITIK = "Kritik"
ONCELIK_YUKSEK = "Yüksek"
ONCELIK_ORTA = "Orta"
ONCELIK_DUSUK = "Düşük"

KRITIKLIK_SECENEKLERI: tuple[str, ...] = (
    ONCELIK_KRITIK,
    ONCELIK_YUKSEK,
    ONCELIK_ORTA,
    ONCELIK_DUSUK,
)

# --- Görev yaşam döngüsü (çoklu durum; rapordaki süreçle uyumlu basitleştirilmiş küme) ---
# Not: İleride kod tarayıcı / tester onayı servisleri bu durumlar arasında geçiş yapacak.
DURUM_BEKLEMEDE = "Beklemede"  # oluşturuldu, henüz üstlenilmedi
DURUM_KODLANIYOR = "Kodlanıyor"
DURUM_KOD_INCELEMEDE = "Kod İncelemede"  # tarayıcı / yükleme sonrası
DURUM_TESTTE = "Test Aşamasında"
DURUM_REVIZYON = "Revizyon"  # tester bug/revize iade
DURUM_TAMAMLANDI = "Tamamlandı"

# --- Tarih biçimi (SQLite TEXT ile ISO; due_date karşılaştırması için) ---
TARIH_ISO = "%Y-%m-%d"
TARIH_SAAT_ISO = "%Y-%m-%d %H:%M:%S"

# --- Bildirim simülasyonu (SMTP yok; uygulama içi kayıt) ---
BILDIRIM_TIP_ATAMA = "GOREV_ATAMA"
BILDIRIM_TIP_TEST = "TEST_GUNCELLEME"
BILDIRIM_TIP_SCRUM = "SCRUM_HATIRLATICI"
BILDIRIM_TIP_GENEL = "GENEL"
BILDIRIM_TIP_EKIP_DAVET = "EKIP_DAVET"
BILDIRIM_TIP_KATILIM_ISTEGI = "KATILIM_ISTEGI"
BILDIRIM_TIP_DAVET_KABUL = "DAVET_KABUL"
BILDIRIM_TIP_KATILIM_ONAY = "KATILIM_ONAY"

DAVET_DURUM_BEKLEMEDE = "beklemede"
DAVET_DURUM_KABUL = "kabul"
DAVET_DURUM_RED = "red"

KATILIM_DURUM_BEKLEMEDE = "beklemede"
KATILIM_DURUM_ONAY = "onaylandi"
KATILIM_DURUM_RED = "reddedildi"

# --- Gönderi görünürlüğü ---
GORUNURLUK_HERKES = "herkes"
GORUNURLUK_BAGLANTI = "baglanti"
GORUNURLUK_EKIP = "ekip"
GORUNURLUK_GIZLI = "gizli"
GORUNURLUK_SECENEKLERI: tuple[str, ...] = (
    GORUNURLUK_HERKES,
    GORUNURLUK_BAGLANTI,
    GORUNURLUK_EKIP,
    GORUNURLUK_GIZLI,
)

# --- Sprint ---
SPRINT_DURUM_AKTIF = "aktif"
SPRINT_DURUM_TAMAMLANDI = "tamamlandi"

BILDIRIM_TIP_DM = "DM"
BILDIRIM_TIP_DUYURU = "EKIP_DUYURU"

# Ek dosya ve avatar kökü
EKLER_DIR = os.path.join(_PROJE_KOKU, "assets", "ekler")
os.makedirs(EKLER_DIR, exist_ok=True)

# --- Arayüz (tek pencere) ---
UI_APP_TITLE = "Taskist Reborn"
UI_DEFAULT_GEOMETRY = "1280x800"
UI_MIN_WIDTH = 1024
UI_MIN_HEIGHT = 680

AVATAR_DEFAULTS_DIR = os.path.join(_PROJE_KOKU, "assets", "avatars", "default")
AVATAR_USER_DIR = os.path.join(_PROJE_KOKU, "assets", "avatars", "users")

# --- Tooltip metinleri (buton kimliği → açıklama) ---
UI_TOOLTIP_METINLERI: dict[str, str] = {
    "giris_yap": "E-posta veya kullanıcı adı ile oturum açın.",
    "kayit_ol": "Yeni hesap oluşturun; ardından giriş yapabilirsiniz.",
    "cikis": "Oturumu kapatır ve giriş ekranına döner.",
    "yeni_ekip": "Yeni çalışma alanı (ekip) oluşturur; siz otomatik Yönetici olursunuz.",
    "ekibe_gir": "Seçilen ekibin rolünüze göre paneline geçer.",
    "tema": "Arayüzü koyu veya açık temaya geçirir.",
    "profilim": "Profilinizi görüntüleyin.",
    "profil_ayarlar": "Profil fotoğrafı, hesap, tema ve çıkış ayarları.",
    "bildirimler": "Okunmamış bildirimlerinizi açar.",
    "geri_ekipler": "Ekip seçim ekranına döner.",
    "ekiplerim": "Çalışma alanları sekmesini açar.",
    "yeni_gorev": "Ekibe yeni görev kartı oluşturur ve geliştiriciye atar.",
    "gorev_duzenle": "Seçili görevin başlık, açıklama ve tarihini günceller.",
    "gorev_sil": "Seçili görevi kalıcı olarak siler.",
    "uye_davet": "Kayıtlı kullanıcıya e-posta veya @kullanici ile davet gönderir.",
    "kullanici_ara": "Kullanıcı adı veya e-posta ile arayıp profile gider.",
    "alt_gorevler": "Ana göreve bağlı alt görev listesini yönetir.",
    "gorev_ustlen": "Görevi üstlenir; durum Kodlanıyor olur ve süre sayacı başlar.",
    "kod_yukle": "Kodu yükler; tarayıcı sonrası test veya revizyon aşamasına geçer.",
    "teste_zorla": "Tarayıcı hatası olsa bile görevi test aşamasına gönderir.",
    "onayla": "Görevi tamamlandı olarak işaretler ve süreyi loglar.",
    "revize": "Görevi revizyon matrisi ile geliştiriciye iade eder.",
    "scrum_gunluk": "Günlük scrum sorularını yanıtlayın.",
    "denetim_gunlugu": "Ekip işlem geçmişini listeler.",
    "performans_raporu": "Görev süre analizi ve ekip verimliliği raporu.",
    "scrum_ozet": "Ekip üyelerinin günlük scrum cevaplarını gösterir.",
    "takip_et": "Bu kullanıcıyı takip ederek güncellemelerinden haberdar olun.",
    "profil_kaydet": "Profil bilgilerinizi ve gizlilik ayarını kaydeder.",
    "dm": "Doğrudan mesajlarınızı açar.",
}
