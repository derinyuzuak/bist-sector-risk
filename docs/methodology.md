# Yöntem / Methodology

## Araştırma kapsamı

2019-01–2024-12 aylık gözlemler. Gerekli önceki dönem verisi yalnızca getiri, yayın geçmişi ve şok standardizasyonu içindir. Sektör başına 72 gözlem vardır; bunlar bağımsız sektör-ay örnekleri olarak havuzlanmaz. Modeller her sektör için ayrıdır.

Bu koşumun endeks evreni `XBANK` (bankacılık) ve `XUSIN` (sanayi) ile sınırlıdır. Her ikisi de yfinance ikincil kaynağında 2017-12–2024-12 için ortak, kesintisiz günlük kapanış kapsamı vermiştir. `XBANK`, geniş mali endeks `XUMAL` ile aynı temsil kapsamına sahip değildir. Enerji, inşaat, ticaret, bilişim ve sağlık/ilaç için sürekliliği doğrulanmış ücretsiz temsilci bulunmadığından bu koşuma alınmamıştır. Bu seçimler ekonomik kapsam sınırlamasıdır; eksik seriler uydurulmaz.

## Girdi ve bilgi zamanı

Günlük kapanışlar sağlayıcının işlem takvimine göre hizalanır. Bir ayda en az 15 seans ve her planlı seansta fiyat gerekir. Bu eşik, takvimin doğru olduğunu kanıtlamaz; takvim kaynağı ayrıca doğrulanır. Eksik fiyatlar doldurulmaz. Eksik ayın kapanışını gerektiren sonraki ay getirisi de geçersizdir. Kriz uç değerleri korunur.

`period` gözlem döneminin sonu, `available_at` bu vintage değerinin bilinebildiği tarihtir. Her tahmin kökeninde bilinen son gözlem döneminin en yeni bilinen revizyonu seçilir. GDP üç aylık olarak saklanır; aylık bilgi setinde son açıklanmış çeyrek kullanılabilir, fakat bu değer yeni aylık üretim gözlemi değildir. Aylık sanayi üretimi ayrı girdidir. Gözlem tarihi asla otomatik yayın tarihi kabul edilmez.

Nominal TRY fiyat endeksleri varsayılan araştırma girdisidir. Aynı portföyde farklı para birimi veya fiyat/toplam-getiri endeksleri karıştırılmamalıdır. Sağlayıcının endeks baz değişimleri süreklilik açısından kontrol edilmelidir. Sonradan revize edilmiş veriler kullanılırsa geriye dönük değerlendirme, gerçek zamanlı performans olarak sunulamaz.

## Hedefler ve şok göstergesi

`return_value = P_month_end / P_previous_month_end - 1`.

`volatility = sample_std(log(P_day / P_previous_session)) * sqrt(252)`.

Volatilite yıllıklaştırılmış gerçekleşen oynaklıktır; standart sapma tanımı kullanılır, kareler toplamının karekökü olan diğer gerçekleşen volatilite tanımlarıyla karıştırılmaz. Hedef bir sonraki ayın getirisi veya oynaklığıdır. Negatif oynaklık tahmini sıfıra kırpılır; portföyde ayrıca %1 yıllık oynaklık tabanı vardır.

Şok ekranı makro serilerin değişimlerini, yalnızca daha önceki en az 12 değişimin genişleyen ortalama/standart sapmasıyla standardize eder. |z| > 2 yalnızca betimleyici eşiktir. Bu yaklaşım sürpriz politika bileşenlerini veya dışsal şokları tanımlamaz.

## ADF ve Toda–Yamamoto

ADF: sabit terim, en fazla 3 gecikme, BIC, %5 eşik; en çok ikinci fark. Sonuç çözümlenemiyorsa test atlanır ve nedeni kaydedilir. Trend varsayımı ve yapısal kırılmalar önemli sınırlılıklardır; birim kök sıfır hipotezinin reddedilememesi onun kanıtı değildir.

İkili makro–hedef sisteminde azami bütünleşme derecesi `dmax` belirlenir. Ortak örneklemde BIC ile `k` seçilir; `k >= max(1,dmax)` ve `k <= 3`. Düzeylerde `VAR(k+dmax)` tahmin edilir. Wald matrisi yalnızca neden değişkeninin ilk `k` gecikmesini kısıtlar; ek gecikmeler serbest kalır. İçsel ay boşlukları kapatılarak zaman sıkıştırılmaz; böyle seriler reddedilir. Artık beyazlık testi kaydedilir ve başarısız tanılamalı testler tahmin değişkeni seçemez.

Benjamini–Hochberg düzeltmesi her sektör–hedef içindeki makro test ailesine uygulanır. Bu, tüm araştırma çapında ailewise hata kontrolü iddiası değildir. Nedensellik yorumları tek yönlü makro→sektör öngörü ilişkileriyle sınırlıdır; ters yön ve yapısal tanımlama yapılmaz.

## Tahmin deneyi

Başlangıç eğitimi: 2019–2022. Doğrulama hedefleri: 2023'ün 12 ayı. Her doğrulama kökeninde yalnızca o tarihe kadar gerçekleşmiş hedefler eğitimde bulunur. Özellik taraması aynı tarih sınırıyla yinelenir. Getiri ve oynaklık geçmişi her zaman dahildir; anlamlı ve tanılaması uygun makro düzeyler/değişimler eklenir. Hiç makro seçilmemesi geçerli sonuçtur.

Ridge alpha: 1 veya 10. XGBoost: 60 ağaç; derinlik 1 veya 2; öğrenme hızı .04; L2=10; minimum çocuk ağırlığı 5; tam satır/sütun örneklemesi; seed=2209. Doğrulama MAE'sine göre her aile kendi ayarını seçer. Ridge medyan doldurma ve standardizasyonu yalnızca eğitimden öğrenir; XGBoost NaN işleyebilir.

2023 sonunda seçim ve model katsayıları dondurulur. 2024'te model yeniden eğitilmez; tahmin girdilerinde o tarihte bilinen son bilgiler kullanılabilir. Temel modeller eğitim hedeflerinin ortalaması ve son bilinen hedef değeridir. Veri sızıntısı testinde 2024 sonuçlarını değiştirmek model seçimini ve Ocak 2024 tahminini değiştirmemelidir.

MAE, RMSE ve geçmiş ortalamaya göre MAE iyileşmesi raporlanır. MAE için 1.000 tekrarlı, üç aylık dairesel blok bootstrap aralığı betimleyici belirsizlik göstergesidir; yalnızca 12 test ayıyla güçlü çıkarım yapılmaz.

## Portföy ve kapsam sınırları

XGBoost'un tahmini oynaklığının tersi normalize edilir. Uzun pozisyon ağırlıkları 1'e toplanır. Karşılaştırma aynı sektör evreninde eşit ağırlıktır. 0/10/25/50 baz puan maliyet, mutlak işlem tutarı üzerinden uygulanır; ilk yatırım dahildir. Dengeleme önceki ayın getiriyle sürüklenmiş ağırlıklarına karşı hesaplanır. Servet 1'den başlar; maksimum düşüş başlangıç servetini de içerir.

Sektör seçimi tüm dönemin veri yeterliliğine bağlıdır; bu geriye dönük sabit araştırma evrenidir ve gerçek zamanlı evren seçimi değildir. Sektörler örtüşebilir. Ağırlıklandırma ve ay sonu fiyatı idealize edilmiştir; gerçek işlem gecikmesi/likidite, vergi ve lisanslı endeks takibi modellenmez. Gerçekleşebilir yatırım getirisi iddia edilmez.
