# GitHub yayını

Bu teslim yerel projedir; uzak depo veya canlı web servisi oluşturulmamıştır.

1. README'deki gerçek kaynak, temsil kapsamı ve vintage sınırlarını koruyun.
2. Yazar adı, varsa danışman rolü ve proje destek durumunu doğrulayın. Başvuru belgesi destek kararı değildir.
3. Kod lisansını proje sahibi seçsin; veri ve çıktı hakları koddan ayrıdır. MIT gibi bir kod lisansı BIST verisini kapsamaz.
4. `data/private`, `.env`, API anahtarları, kişisel dosyalar ve sanal ortamı commit etmeyin. Türetilmiş `results/research` dosyaları kaynak kullanım koşulları doğrulandıktan sonra eklenebilir. `.gitignore` eklenmiş olsa da `git diff --cached` ile inceleyin.
5. Testleri, sonuç doğrulamasını ve gerçek veri notebook'larını çalıştırın. `docs/validation.md` yerel doğrulamayı gösterir; GitHub Actions rozeti yalnızca uzak CI gerçekten çalıştıktan sonra eklenmelidir.
6. Depo adı önerisi: `bist-sector-risk`. Açıklama: “Notebook-led ADF, Toda–Yamamoto and XGBoost research for BIST sector risk.” Konular: `econometrics`, `time-series`, `xgboost`, `bist`, `reproducible-research`.
7. GitHub'da hedef hesap/depo netleştiğinde yerel içeriği bu depoya gönderin. Uzak `push` işleminden önce proje sahibinin son onayını alın.

İlk sürüm notu veri kaynaklarını, iki endeksle sınırlı temsil kapsamını, son değerlendirme dönemini ve yeniden üretim komutlarını belirtmelidir.
