# Veri temini ve sözleşmesi / Data contract

## Mevcut erişim durumu

21 Eylül 2026 kontrolünde EVDS3 güncel resmî kılavuzu API anahtarı gerektiriyor. Anahtar yerel, Git tarafından yok sayılan dosyadan kullanılarak 2017-12–2024-12 için gerçek makro ham verisi indirildi. Kullanıcı onayıyla yfinance üzerinden `XBANK.IS` ve `XUSIN.IS` için 2017-12–2024-12 günlük kapanışlar indirildi; bu iki endeksin gerçek verili araştırma sonuçları `results/research/` altında türetilmiş çıktı olarak kaydedildi. Ham fiyatlar, makro yanıtlar ve anahtarlar `data/private/` altında kalır. Borsa İstanbul tarihsel veri sayfası DataStore'a yönlendirir; bu koşumda lisanslı BIST arşiv dosyası kullanılmadı. Bu nedenle bulgular yalnızca iki ikincil-kaynak endeksinin temsil kapsamıyla sınırlıdır; geniş sektör evreni veya resmî tarihsel vintage doğrulanmış değildir.

- [EVDS3 web servis kılavuzu](https://evds3.tcmb.gov.tr/igmevdsms-dis/documents/showDocument?docId=8)
- [Borsa İstanbul tarihsel veri erişimi](https://www.borsaistanbul.com/veriler/gecmise-donuk-veri-satisi)
- [Borsa İstanbul veri kullanım/dağıtım bilgisi](https://www.borsaistanbul.com/sss/veri-dagitim-ve-endeks-lisanslama)
- [TÜİK GSYİH](https://veriportali.tuik.gov.tr/tr/press/54161)

Veri satın alınmaz. Üniversite üzerinden ücretsiz erişim sağlanırsa kullanım ve yayımlama kapsamı ayrıca kaydedilir. Bir sitede görünür olması verinin yeniden paylaşılabileceği anlamına gelmez.

## Dört girdi dosyası

UTF-8 CSV, ondalık ayırıcı nokta, tarih ISO `YYYY-MM-DD`. Dosyalar aynı klasörde tutulur. Gerçek veriler `data/private/study/` altında kalmalıdır.

| Dosya | Gerekli sütunlar | Açıklama |
|---|---|---|
| prices.csv | date, sector, close | Her işlem gününün pozitif, sonlu kapanışı; her sektör/tarih tekil |
| calendar.csv | date | Kaynakla doğrulanmış BIST işlem seansları; hafta içi varsayımı gerçek veri için yeterli değildir |
| macro.csv | series, period, available_at, value | Dönem sonu, o vintage'ın bilinebilir tarihi, sonlu değer; her seri/dönem/yayın tekil |
| provenance.json | mode, calendar, series | Bu proje için `mode` değeri `research` |

`series` her endeks ve makro seri için şu dolu alanları içermelidir: `source_url`, `retrieved_at`, `unit`, `frequency`, `transformation`, `redistribution`, `vintage_policy`. `calendar` alanına takvim kaynağı yazılır.

Makro seri anahtarları: `policy_rate` (%), `usdtry` (TRY/USD), `cpi` (endeks), `brent` (USD/varil), `industrial_production` (endeks), `gdp_growth` (%). Model makro sütunlarını girdiden keşfeder. Gerçek seri kodları metaveri ve tarih kapsamı doğrulanmadan tahmin edilmez. CPI düzeyi ve değişimi kullanılır; yıllık enflasyon oranıyla eşdeğer oldukları iddia edilmez.

Tarihsel ilk yayın/revizyonlar temin edilemiyorsa, bugünkü revize değerlerin geçmiş yayın tarihleriyle birleştirildiği çalışma açıkça `latest-revised pseudo-real-time` diye kaydedilmelidir. Ekonomik verilerde gerçek zamanlı performans kanıtı üretmez. Yayımlanma tarihi bilinmeyen satırlar tahmin analizine alınmamalıdır.

## EVDS raw indirme

API anahtarını asla sohbete, README'ye veya GitHub'a yazmayın. Varsayılan güvenli konum, Git tarafından yok sayılan `data/private/evds.key` dosyasıdır. Dosyada `EVDS_API_KEY=...` biçiminde tek anahtar bulunabilir; işlem bittiğinde silinebilir. Alternatif olarak yalnızca yerel terminalde `EVDS_API_KEY` ortam değişkeni kullanılabilir.

```powershell
# EVDS_API_KEY değişkenini yerel terminalinizde tanımladıktan sonra:
python -m bist_risk.cli fetch-evds --series TP.DK.USD.A --start 01-12-2017 --end 31-12-2024
```

Komut güncel EVDS3 adresine başlık üzerinden kimlik doğrular, günlük gözlem sınırına karşı yıllık parçalara böler ve yanıtları `data/private/evds` altında tutar. Farklı frekanstaki seriler ortak tarih kesişimine düşürülmemesi için ayrı isteklerle indirilir.

Bu araştırma için doğrulanmış seri eşlemesi ve dönüşüm komutu şöyledir:

```powershell
python -m bist_risk.cli fetch-evds --series TP.DK.USD.A TP.BRENTPETROL.EUBP TP.GENENDEKS.T1 TP.TSANAYMT2021.BCD TP.GSYIH60.HY.B1GQ TP.BISPOLFAIZ.TUR --start 01-12-2017 --end 31-12-2024 --out data/private/evds-real
python -m bist_risk.cli prepare-evds --raw data/private/evds-real --out data/private/study-macro
```

Eşleme USD/TL, Brent, TÜFE, mevsim ve takvim etkisinden arındırılmış sanayi üretimi, Türkiye politika faizi (EVDS içindeki BIS serisi) ve zincirlenmiş-hacim GSYİH'nın çeyreklik değişiminden oluşur. `prepare-evds`, aylık tahmin bilgi kümesinde ileri dönem gözlemini engellemek için gözlem sonunda 0/35/60/100 günlük koruyucu bekleme süreleri kullanır. Bunlar ilk yayım tarihleri değildir: çıktı açıkça `latest revised` kalır ve gerçek zamanlı tahmin kanıtı sayılmaz.

API başarısı, BIST fiyat verisi olmadan gerçek veri hattının uçtan uca doğrulandığı anlamına gelmez. Anahtarsız ve sahte yanıt testleri gerçek servis erişiminin yerine geçmez.

## Yfinance ikincil fiyat kaynağı

Kullanıcı onayıyla yfinance, Borsa İstanbul arşivine ikincil kaynak olarak eklenmiştir. 21 Eylül 2026 tarihli kapsam denetiminde yalnızca `XBANK.IS` (bankacılık) ve `XUSIN.IS` (sanayi) sembolleri 1 Aralık 2017–31 Aralık 2024 için kesintisiz ortak günlük kapanış sağlamıştır. `XBANK`, geniş mali endeks `XUMAL` ile aynı temsil kapsamına sahip değildir. Yahoo'da sürekli serisi bulunmayan enerji, inşaat, ticaret ve bilişim temsilcileri bu gerçek veri koşumundan dışarıda bırakılır.

```powershell
python -m bist_risk.cli prepare-yahoo --out data/private/study-prices-yahoo-real
python -m bist_risk.cli assemble-study --prices data/private/study-prices-yahoo-real --macro data/private/study-macro --out data/private/study-yahoo-real
python -m bist_risk.cli validate --data data/private/study-yahoo-real --mode research
python scripts/execute_notebooks.py
```

Yfinance belgeleri, Yahoo Finance API'sinin kişisel kullanım için tasarlandığını belirtir. Yfinance ile indirilen ham fiyat verisi `data/private/` altında kalır ve GitHub'a eklenmez. Proje sahibinin açık izniyle yalnızca türetilmiş araştırma tabloları, rapor ve manifest `results/research/` altında sürüm kontrolüne alınabilir; yayımlamadan önce Yahoo Finance kullanım koşulları bağımsız olarak tekrar kontrol edilmelidir. Veri, BIST'in resmî tarihsel vintage kaydı değildir. Daha geniş veya kamusal bir ampirik çalışma için resmî BIST veri lisansı ya da açıkça yeniden paylaşılabilir alternatif kaynak gerekir.

Yfinance koşumunda Mayıs 2021'de yalnızca 13 ortak BIST işlem seansı vardır. Her iki endekste de bu 13 seansın tamamı mevcut olduğundan `config.toml` alt sınırı 10 olarak kaydedilir; bu istisna eksik fiyat doldurma değildir.

## Kalite kapısı

Tam dönem için geçerli aylık getiri ve oynaklığı olmayan sektör dışlanır. Eksik sektörler `quality.csv` içinde açıklanır. Hiç sektör geçmezse analiz durur. Veri satın alma, ücretli hizmete üyelik veya ham veriyi yayımlama yapılmaz. Takvimde eksik seans, para birimi karışması ve endeks yeniden bazlama gibi kaynak sorunları sağlayıcıyla kontrol edilmelidir.
