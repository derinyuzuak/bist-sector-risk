# Doğrulama kaydı / Validation record

Son çalışma: 21 Eylül 2026, yerel Windows ortamı, Python 3.12.

| Kontrol | Sonuç | Kanıt |
|---|---|---|
| Birim testleri | Başarılı | 23 passed |
| EVDS ayrı-frekans hazırlığı | Başarılı | 6 resmi seri, 453 makro gözlemi; günlük/aylık/çeyreklik kesişim kaybı önlendi |
| Yfinance ikincil kaynak koşumu | Başarılı | XBANK ve XUSIN için 1.758 ortak günlük seans, 72 aylık kapsam; ham veri yerelde tutuldu |
| Gerçek uçtan uca analiz | Başarılı | XBANK ve XUSIN, her birinde 72 ay; 2024 için 12 aylık dış örnek tahmini |
| Sonuç bütünlüğü | Başarılı | Girdi/çıktı SHA-256 özetleri, zaman sırası, 2024 test kapsamı ve ağırlık toplamları doğrulandı |
| Notebook'lar | Başarılı | Dört gerçek veri notebook'u uçtan uca yürütüldü ve sonuç manifestini üretti |
| Arayüz | Başarılı | Türkçe ve İngilizce altı ekran Streamlit test ortamında hatasız oluşturuldu |
| Bağımlılıklar | Başarılı | `pip check`: broken requirements yok |

## Çalıştırılan komutlar

```powershell
python -m pytest -q
python scripts/verify_results.py results/research
python scripts/execute_notebooks.py
python -m pytest tests/test_app.py -q
python -m pip check
```

## Kapsam sınırı

Bu kayıt gerçek EVDS/yfinance koşumunu doğrular. Borsa İstanbul fiyat/endeks arşiviyle daha geniş temsil kapsamına geçildiğinde işlem takvimi, gözlem birimleri ve yayın/vintage zamanları yeniden denetlenmelidir.

EVDS raw indirme ve `prepare-evds` dönüşümü gerçek makro kaynakla doğrulandı; bu doğrulama tek başına sektör getirisi, oynaklığı, nedensellik, tahmin veya portföy sonucunu doğrulamaz.

Kullanıcı yetkilendirmesiyle yürütülen yfinance koşumunda `scripts/verify_results.py results/research` gerçek kaynaklı çıktıların zaman sırasını, hash'lerini, tahminlerin son dönem kapsamını ve ağırlıklarını doğruladı. Ham kaynak dosyaları ve API anahtarları yalnızca `data/private/` altında tutulur.
