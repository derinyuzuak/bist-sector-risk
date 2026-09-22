# Borsa İstanbul’da Makroekonomik Şoklar ve Yatırımcı Risk Algısı


**Gerçek veriyle yeniden üretilebilir makroekonomik risk analizi.**


[English](README.md) · [Yöntem](docs/methodology.md) · [Veri rehberi](docs/data.md) · [Kaynakça](docs/references.md)


Bu depo, Ocak 2019–Aralık 2024 dönemi için ADF, Toda–Yamamoto ve XGBoost çerçevesini gerçek verilerle uygular. Kaydedilmiş sonuçlar, günlük `XBANK` ve `XUSIN` endeks kapanışları ile EVDS makro serilerinden üretilmiştir. Ham veriler ve API anahtarları depoda yer almaz. Araştırmanın ana yüzü çalıştırılmış Jupyter notebooklarıdır; `src/` yalnızca tekrar kullanılabilir hesaplama yardımcılarını içerir.


> **Kapsam:** `XBANK`, bankacılık endeksidir; geniş mali endeksin tam karşılığı değildir. `XUSIN` sanayi endeksidir. Yahoo Finance'ta kesintisiz tarihsel kapsamı doğrulanmayan temsilciler dışlanmıştır. Bulgular iki endeks, 72 ay ve 12 aylık son değerlendirme dönemiyle sınırlıdır.


## Çalıştırma


Python 3.12 önerilir.


```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python scripts\verify_results.py results\research
.\.venv\Scripts\python scripts\execute_notebooks.py
.\.venv\Scripts\python -m streamlit run app.py
```


Arayüz ve notebook'lar varsayılan olarak `results/research/` içindeki kaydedilmiş gerçek sonuçları kullanır. Ham girdi olmadan sonuçlar incelenebilir; analizi baştan çalıştırmak için aşağıdaki yerel veri hazırlığı gerekir.


## Gerçek veri hattını yeniden çalıştırma


EVDS anahtarını yalnızca Git tarafından yok sayılan `data/private/evds.key` dosyasında tutun. Anahtarı sohbete veya depoya yazmayın.


```powershell
python -m bist_risk.cli fetch-evds --series TP.DK.USD.A TP.BRENTPETROL.EUBP TP.GENENDEKS.T1 TP.TSANAYMT2021.BCD TP.GSYIH60.HY.B1GQ TP.BISPOLFAIZ.TUR --start 01-12-2017 --end 31-12-2024 --out data/private/evds-real
python -m bist_risk.cli prepare-evds --raw data/private/evds-real --out data/private/study-macro
python -m bist_risk.cli prepare-yahoo --out data/private/study-prices-yahoo
python -m bist_risk.cli assemble-study --prices data/private/study-prices-yahoo --macro data/private/study-macro --out data/private/study-yahoo-real
python -m bist_risk.cli validate --data data/private/study-yahoo-real --mode research
python scripts/execute_notebooks.py
```


Yfinance ikincil kaynaktır; resmi BIST ZIP/CSV dosyaları erişilebildiğinde `prepare-bist` komutu aynı şemayı üretir. Kaynak, dönüşüm, indirme zamanı ve vintage sınırı her koşumun `manifest.json` dosyasında kaydedilir.


## Ne içerir?


| Konum | İçerik |
|---|---|
| `results/research/` | Türetilmiş gerçek sonuç tabloları, otomatik Türkçe rapor ve doğrulama manifesti |
| `notebooks/` | Araştırma kararlarını ve gerçek veri analizini hücre hücre gösteren dört notebook |
