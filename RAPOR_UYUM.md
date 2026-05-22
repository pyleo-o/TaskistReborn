# Rapor – Uygulama Uyum Rehberi

Bu dosya, **Taskist Reborn** ile final raporunuzun aynı dili konuşması içindir.

## Uyumlu (raporda yazabilirsiniz)

| Rapor iddiası | Uygulamada kanıt |
|---------------|------------------|
| Rol: Yönetici, Backend, Frontend, Tester | `Ekip_Uyeleri` + davet paneli rol seçimi |
| Kod tarayıcı (AST) | `CodeScannerService` + geliştirici paneli |
| Kritiklik matrisi | `KRITIKLIK_SECENEKLERI`, Kanban üst sıra |
| Otomatik süre raporu | `AnalyticsService`, `Islem_Loglari` |
| Günlük Scrum | `ScrumDialog` (ekibe girince), yönetici özeti |
| @kullanici arama / davet | Yönetici paneli arama + davet |
| Kod temiz → Test aşaması | `kod_yukle_ve_teste_gonder` |
| İşlem geçmişi | `AuditService`, Denetim sekmesi |
| Alt görevler | `AltGorevler` + yönetici detay penceresi |
| Son teslim kırmızı vurgu | `due_date_gecikmis_mi` |
| Koyu tema, kısayollar | Ctrl+H, Ctrl+F, Ctrl+M, Ctrl+K |
| Bildirim + e-posta simülasyonu | Bildirim merkezi + `logs/email_simulation.log` |
| Yoğunluk uyarısı (senaryo A1) | Atamada aktif görev eşiği (`AKTIF_GOREV_UYARI_ESIGI`) |

## Raporda düzeltmeniz gereken (kod değil)

| Raporda yanlış | Doğrusu (proje) |
|----------------|-----------------|
| MySQL | **SQLite** (`taskist_reborn.db`) |
| SMTP gerçek e-posta | **Simülasyon** (log dosyası) |
| Bekliyor / Testte / Geliştiriliyor | **Beklemede / Test Aşamasında / Kodlanıyor** |
| Rol kullanıcı tablosunda | Rol **ekip üyeliğinde** |
| ER 4 tablo | **Ekipler, Ekip_Uyeleri, AltGorevler, ScrumGunluk, Bildirimler** de var |

## Kısmi / yorumla anlatın

| Rapor ifadesi | Gerçek |
|---------------|--------|
| Kod hatasını tek tıkla Tester’a ayrı bug kartı | Aynı görev teste gider; ayrı bug kaydı yok |
| %100 gerçekleştirildi | “Temel modüller tamamlandı” deyin |
| İnternet kesilse de çalışır | Yerel SQLite; sunucu yok |

## GitHub

https://github.com/pyleo-o/TaskistReborn
