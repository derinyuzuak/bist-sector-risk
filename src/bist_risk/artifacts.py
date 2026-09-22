"""Small, non-analytical helpers for versioning notebook-produced results."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform

import pandas as pd


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_tables(output: Path, tables: dict[str, pd.DataFrame]) -> None:
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(output / f"{name}.csv", index=False)


def create_manifest(output: Path, config: dict, provenance: dict, sectors: list[str], input_folder: Path, tables: dict[str, pd.DataFrame]) -> dict:
    """Record reproducibility metadata after notebooks have produced every table."""
    output, input_folder = Path(output), Path(input_folder)
    versions = {name: importlib.metadata.version(name) for name in [
        "numpy", "pandas", "scipy", "statsmodels", "scikit-learn", "xgboost", "streamlit", "yfinance"
    ]}
    manifest = dict(
        mode="research",
        empirical_findings=True,
        created_at=datetime.now(timezone.utc).isoformat(),
        python=platform.python_version(),
        packages=versions,
        config=config,
        sectors=sectors,
        input_hashes={name: sha256(input_folder / name) for name in ["prices.csv", "macro.csv", "calendar.csv", "provenance.json"]},
        provenance=provenance,
        caveats=[
            "Volatility is a proxy, not directly measured investor perception.",
            "The final 2024 evaluation has only 12 monthly outcomes per sector and target.",
            "Predictive Granger relationships do not identify structural causal effects.",
            "Latest revised macro data with availability guards is not a first-release vintage dataset.",
            "Index-return portfolio results are a non-levered research simulation, not investment advice.",
        ],
    )
    manifest["result_hashes"] = {name: sha256(output / f"{name}.csv") for name in tables}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def write_turkish_report(output: Path, manifest: dict) -> None:
    """Render a short report from the notebook-produced result tables."""
    output = Path(output)
    metrics = pd.read_csv(output / "metrics.csv")
    portfolio = pd.read_csv(output / "portfolio_summary.csv")
    quality = pd.read_csv(output / "quality.csv")
    config = manifest["config"]
    report = f"""# BIST Sektörel Risk Araştırması

**GERÇEK VERİ ANALİZİ — KAYNAK, TEMSİL KAPSAMI VE VINTAGE SINIRLARINI İNCELEYİN**

## Araştırma tasarımı

Dönem: {config['study']['start']} – {config['study']['end']}. Eğitim: 2019–2022; model seçimi: 2023; son değerlendirme: 2024. Günlük log getirilerin standart sapmasından yıllıklaştırılan gerçekleşen oynaklık, risk algısının dolaylı piyasa göstergesidir.

ADF sabit terimli ve BIC gecikme seçimli uygulanır. Toda–Yamamoto testinde düzeylerde VAR(k+dmax) kurulur; Wald kısıtları yalnızca ilk k gecikmeye uygulanır. Tam örneklem nedensellik tabloları açıklayıcıdır. Tahmin değişkenleri yalnızca ilgili eğitim diliminde seçilir.

## Veri kapsamı

{quality.to_markdown(index=False)}

## 2024 tahmin başarısı

MAE ve RMSE ondalık birimdedir. MAE aralığı üç aylık dairesel blok bootstrap ile hesaplanır; 12 sonuç gözlemi nedeniyle kesinlik sınırlıdır.

{metrics.to_markdown(index=False, floatfmt='.4f')}

## Portföy araştırma simülasyonu

Tahmini oynaklığın tersiyle ağırlıklandırılan kaldıraçsız aylık endeks portföyü eşit ağırlıkla karşılaştırılır. Maliyet, mutlak alım-satım tutarı üzerinden uygulanır.

{portfolio.to_markdown(index=False, floatfmt='.4f')}

## Sınırlılıklar

- Bu sonuçlar manifestte kayıtlı iki endeks ve kaynak kapsamıyla sınırlıdır.
- Granger öngörü ilişkisi yapısal neden-sonuç kanıtı değildir.
- Makro serilerdeki revizyonlar gerçek zamanlı bilgi setini tam yansıtmayabilir.
- Endeks portföyü yatırım yapılabilir bir fon veya kişisel yatırım tavsiyesi değildir.

## İzlenebilirlik

Ham veri depoda yer almaz. Girdi/çıktı SHA-256 özetleri, paket sürümleri, ayarlar ve kaynak bilgileri `manifest.json` içinde; ayrıntılı test ve model çıktıları ilgili CSV dosyalarındadır.
"""
    (output / "report_tr.md").write_text(report, encoding="utf-8")
