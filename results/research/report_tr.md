# BIST Sektörel Risk Araştırması

**GERÇEK VERİ ANALİZİ — KAYNAK, TEMSİL KAPSAMI VE VINTAGE SINIRLARINI İNCELEYİN**

## Araştırma tasarımı

Dönem: 2019-01-01 – 2024-12-31. Eğitim: 2019–2022; model seçimi: 2023; son değerlendirme: 2024. Günlük log getirilerin standart sapmasından yıllıklaştırılan gerçekleşen oynaklık, risk algısının dolaylı piyasa göstergesidir.

ADF sabit terimli ve BIC gecikme seçimli uygulanır. Toda–Yamamoto testinde düzeylerde VAR(k+dmax) kurulur; Wald kısıtları yalnızca ilk k gecikmeye uygulanır. Tam örneklem nedensellik tabloları açıklayıcıdır. Tahmin değişkenleri yalnızca ilgili eğitim diliminde seçilir.

## Veri kapsamı

| sector   | eligible   |   months | reason   |
|:---------|:-----------|---------:|:---------|
| XBANK    | True       |       72 | complete |
| XUSIN    | True       |       72 | complete |

## 2024 tahmin başarısı

MAE ve RMSE ondalık birimdedir. MAE aralığı üç aylık dairesel blok bootstrap ile hesaplanır; 12 sonuç gözlemi nedeniyle kesinlik sınırlıdır.

| sector   | target     | model           |   n |    mae |   rmse |   mae_low |   mae_high |   baseline_mae |   mae_improvement |
|:---------|:-----------|:----------------|----:|-------:|-------:|----------:|-----------:|---------------:|------------------:|
| XBANK    | return     | historical_mean |  12 | 0.0792 | 0.1006 |    0.0535 |     0.1061 |         0.0792 |            0.0000 |
| XBANK    | return     | persistence     |  12 | 0.1124 | 0.1408 |    0.0657 |     0.1738 |         0.0792 |           -0.4195 |
| XBANK    | return     | ridge           |  12 | 0.0769 | 0.0969 |    0.0503 |     0.1030 |         0.0792 |            0.0283 |
| XBANK    | return     | xgboost         |  12 | 0.0720 | 0.0907 |    0.0463 |     0.0968 |         0.0792 |            0.0902 |
| XBANK    | volatility | historical_mean |  12 | 0.0514 | 0.0613 |    0.0338 |     0.0743 |         0.0514 |            0.0000 |
| XBANK    | volatility | persistence     |  12 | 0.0767 | 0.1002 |    0.0458 |     0.1095 |         0.0514 |           -0.4934 |
| XBANK    | volatility | ridge           |  12 | 0.0673 | 0.0775 |    0.0479 |     0.0911 |         0.0514 |           -0.3103 |
| XBANK    | volatility | xgboost         |  12 | 0.0589 | 0.0681 |    0.0392 |     0.0844 |         0.0514 |           -0.1463 |
| XUSIN    | return     | historical_mean |  12 | 0.0595 | 0.0689 |    0.0435 |     0.0795 |         0.0595 |            0.0000 |
| XUSIN    | return     | persistence     |  12 | 0.0730 | 0.0955 |    0.0473 |     0.1043 |         0.0595 |           -0.2279 |
| XUSIN    | return     | ridge           |  12 | 0.0568 | 0.0646 |    0.0430 |     0.0720 |         0.0595 |            0.0450 |
| XUSIN    | return     | xgboost         |  12 | 0.0436 | 0.0563 |    0.0248 |     0.0647 |         0.0595 |            0.2664 |
| XUSIN    | volatility | historical_mean |  12 | 0.0535 | 0.0578 |    0.0427 |     0.0644 |         0.0535 |            0.0000 |
| XUSIN    | volatility | persistence     |  12 | 0.0651 | 0.0795 |    0.0486 |     0.0836 |         0.0535 |           -0.2184 |
| XUSIN    | volatility | ridge           |  12 | 0.0495 | 0.0564 |    0.0377 |     0.0597 |         0.0535 |            0.0746 |
| XUSIN    | volatility | xgboost         |  12 | 0.0555 | 0.0677 |    0.0418 |     0.0692 |         0.0535 |           -0.0378 |

## Portföy araştırma simülasyonu

Tahmini oynaklığın tersiyle ağırlıklandırılan kaldıraçsız aylık endeks portföyü eşit ağırlıkla karşılaştırılır. Maliyet, mutlak alım-satım tutarı üzerinden uygulanır.

| strategy             |   cost_bps |   total_return |   max_drawdown |   months |
|:---------------------|-----------:|---------------:|---------------:|---------:|
| inverse_forecast_vol |          0 |         0.3439 |        -0.1707 |       12 |
| inverse_forecast_vol |         10 |         0.3413 |        -0.1710 |       12 |
| inverse_forecast_vol |         25 |         0.3374 |        -0.1715 |       12 |
| inverse_forecast_vol |         50 |         0.3310 |        -0.1722 |       12 |
| equal_weight         |          0 |         0.3917 |        -0.1782 |       12 |
| equal_weight         |         10 |         0.3897 |        -0.1783 |       12 |
| equal_weight         |         25 |         0.3867 |        -0.1784 |       12 |
| equal_weight         |         50 |         0.3817 |        -0.1786 |       12 |

## Sınırlılıklar

- Bu sonuçlar manifestte kayıtlı iki endeks ve kaynak kapsamıyla sınırlıdır.
- Granger öngörü ilişkisi yapısal neden-sonuç kanıtı değildir.
- Makro serilerdeki revizyonlar gerçek zamanlı bilgi setini tam yansıtmayabilir.
- Endeks portföyü yatırım yapılabilir bir fon veya kişisel yatırım tavsiyesi değildir.

## İzlenebilirlik

Ham veri depoda yer almaz. Girdi/çıktı SHA-256 özetleri, paket sürümleri, ayarlar ve kaynak bilgileri `manifest.json` içinde; ayrıntılı test ve model çıktıları ilgili CSV dosyalarındadır.
