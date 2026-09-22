"""Read-only bilingual presentation of versioned notebook-produced outputs."""
from pathlib import Path
import json
import os
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="BIST · Sector Risk Lab", page_icon="◈", layout="wide")
language = st.sidebar.radio("Dil / Language", ["Türkçe", "English"])
tr = language == "Türkçe"
def t(a, b):
    return a if tr else b

st.markdown("""<style>
.stApp {background:#0c1420;color:#e8edf5}
h1,h2,h3 {letter-spacing:-.035em}
[data-testid="stMetric"] {background:#152337;padding:18px;border:1px solid #263a52;border-radius:12px}
[data-testid="stSidebar"] {background:#101c2c}
.eyebrow {color:#52d8be;font-size:.78rem;letter-spacing:.18em;font-weight:700}
</style>""", unsafe_allow_html=True)
st.sidebar.markdown("## ◈ Sector Risk Lab")
st.sidebar.caption(t("Yeniden üretilebilir finans araştırması", "Reproducible financial research"))
out = Path(os.environ.get("BIST_RESULTS_DIR", str(ROOT / "results/research")))
if not (out / "manifest.json").exists():
    st.info(t("Önce gerçek veri hazırlama ve `python scripts/execute_notebooks.py` komutunu çalıştırın.", "Prepare research data and run `python scripts/execute_notebooks.py` first."))
    st.stop()
manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
st.markdown('<div class="eyebrow">RESEARCH / 2019—2024</div>', unsafe_allow_html=True)
st.title(t("Makro şoklar. Sektörel risk.", "Macro shocks. Sector risk."))
st.caption(t("Borsa İstanbul araştırma çerçevesi · ADF → Toda–Yamamoto → XGBoost", "Borsa Istanbul research framework · ADF → Toda–Yamamoto → XGBoost"))
st.info(t("GERÇEK VERİ — Kaynak, revizyon, temsil kapsamı ve örneklem sınırlılıklarını inceleyin.", "RESEARCH DATA — Review source, vintage, representation and sample limitations."))

def table(name):
    return pd.read_csv(out / f"{name}.csv")

def chart(fig):
    fig.update_layout(template="plotly_dark", paper_bgcolor="#0c1420", plot_bgcolor="#0c1420", font=dict(family="Arial", color="#dbe7f6"), legend_title_text="", margin=dict(l=10,r=10,t=30,b=10))
    st.plotly_chart(fig, width="stretch")

monthly, met = table("monthly"), table("metrics")
c1,c2,c3,c4 = st.columns(4)
c1.metric(t("Sektör", "Sectors"), len(manifest["sectors"]))
c2.metric(t("Sektör başına ay", "Months per sector"), monthly.date.nunique())
c3.metric(t("Son test", "Final holdout"), "2024")
c4.metric(t("Veri türü", "Data mode"), t("Gerçek", "Research"))
pages = [t("Genel bakış", "Overview"), t("Veri kalitesi", "Data quality"), t("Sektörler ve şoklar", "Sectors & shocks"), t("Nedensellik", "Causality"), t("Tahmin başarısı", "Forecast performance"), t("Portföy", "Portfolio")]
page = st.sidebar.radio(t("Araştırmayı keşfet", "Explore the research"), pages)
sector = st.sidebar.selectbox(t("Sektör endeksi", "Sector index"), manifest["sectors"])
st.sidebar.caption(t("Oynaklık risk algısının dolaylı göstergesidir. Yatırım tavsiyesi değildir.", "Volatility is a proxy for risk perception. Not investment advice."))
if page == pages[0]:
    left, right = st.columns([2,1])
    with left:
        st.subheader(t("Araştırma sorusu", "Research question"))
        st.write(t("Makroekonomik değişimler sektör getirileri ve oynaklığının öngörülmesine katkı sağlıyor mu?", "Do macroeconomic changes help forecast sector returns and volatility?"))
        chart(px.line(monthly, x="date", y="volatility", color="sector", labels={"volatility":t("Yıllıklaştırılmış oynaklık", "Annualized volatility"),"date":""}, color_discrete_sequence=px.colors.qualitative.Safe))
    with right:
        st.subheader(t("Araştırma akışı", "Research flow"))
        st.markdown(t("1. Kaynak ve veri kapsamı kontrolü\n2. Yayın tarihine göre hizalama\n3. ADF ve gecikmeli VAR\n4. Eğitim içinde değişken seçimi\n5. Zamana sıralı model karşılaştırması\n6. Maliyetli portföy simülasyonu", "1. Source and coverage audit\n2. Release-time alignment\n3. ADF and lag-augmented VAR\n4. Training-only feature selection\n5. Chronological model comparison\n6. Portfolio simulation with costs"))
        st.download_button(t("Türkçe raporu indir", "Download Turkish report"), (out/"report_tr.md").read_bytes(), "report_tr.md")
        st.download_button(t("Çalıştırma kaydını indir", "Download run manifest"), (out/"manifest.json").read_bytes(), "manifest.json")
elif page == pages[1]:
    st.subheader(t("Kapsam ve veri kökeni", "Coverage and provenance"))
    st.dataframe(table("quality"), hide_index=True, width="stretch")
    st.json(manifest["provenance"])
    st.caption(t("İşlem takvimi ve kaynak sınırları manifestte kayıtlıdır.", "The manifest records the trading-calendar and source limitations."))
elif page == pages[2]:
    st.subheader(sector)
    g = monthly[monthly.sector == sector]
    chart(px.bar(g, x="date", y="return_value", labels={"return_value":t("Aylık getiri", "Monthly return"),"date":""}, color_discrete_sequence=["#52d8be"]))
    shocks = table("shocks")
    series = st.selectbox(t("Makro gösterge", "Macro series"), [c for c in shocks if c != "date"])
    fig = px.line(shocks, x="date", y=series)
    fig.add_hline(y=2, line_dash="dot"); fig.add_hline(y=-2, line_dash="dot")
    chart(fig)
    st.caption(t("Z puanları yalnızca geçmiş değişimlere dayanır. ±2 eşiği betimseldir; yapısal şok tanımlaması değildir.", "Z scores use prior changes only. ±2 is descriptive, not structural shock identification."))
elif page == pages[3]:
    st.subheader(t("Öngörü ilişkileri", "Predictive relationships"))
    st.info(t("Tam örneklem sonuçları açıklayıcıdır. Bunlar ekonomik neden–sonuç kanıtı değildir; modeldeki seçim eğitim geçmişinde ayrıca yapılır.", "Full-sample results are descriptive, not evidence of structural causation. Model screening is repeated within training history."))
    c = table("causality")
    st.dataframe(c[c.sector == sector], hide_index=True, width="stretch")
    a = table("adf")
    with st.expander(t("ADF ayrıntıları", "ADF details")):
        st.dataframe(a[a.sector == sector], hide_index=True)
elif page == pages[4]:
    st.subheader(t("Görülmemiş 2024 hedefleri", "Unseen 2024 targets"))
    target = st.selectbox(t("Hedef", "Target"), ["return", "volatility"])
    m = met[(met.sector == sector) & (met.target == target)]
    fig = px.bar(m, x="model", y="mae", error_y=m.mae_high-m.mae, error_y_minus=m.mae-m.mae_low,
                 labels={"mae":"MAE", "model":""}, color_discrete_sequence=["#52d8be"])
    chart(fig)
    st.dataframe(m, hide_index=True, width="stretch")
    p = table("predictions")
    p = p[(p.sector == sector) & (p.target == target)]
    actual = p[p.model == "xgboost"][["target_date", "actual"]].rename(columns={"actual":"value"}).assign(model=t("Gerçekleşen", "Actual"))
    long = pd.concat([p[["target_date", "prediction", "model"]].rename(columns={"prediction":"value"}), actual])
    chart(px.line(long, x="target_date", y="value", color="model"))
    st.caption(t("Aralıklar 3 aylık blok bootstrap ile hesaplanır. 12 gözlemden güçlü genelleme yapılmaz.", "Intervals use a 3-month block bootstrap. Twelve observations limit generalization."))
else:
    st.subheader(t("Endeks tabanlı araştırma simülasyonu", "Index-based research simulation"))
    port = table("portfolio")
    cost = st.select_slider(t("İşlem maliyeti (baz puan)", "Transaction cost (basis points)"), options=sorted(port.cost_bps.unique()))
    chart(px.line(port[port.cost_bps == cost], x="date", y="wealth", color="strategy", labels={"wealth":t("Başlangıç = 1", "Initial wealth = 1"), "date":""}))
    st.dataframe(table("portfolio_summary"), hide_index=True, width="stretch")
    st.caption(t("Başlangıç alımı ve ağırlık sürüklenmesi maliyete dahildir. Endeksler doğrudan alınıp satılabilir araçlar değildir.", "Costs include initial deployment and weight drift. Indices are not directly tradable instruments."))
st.divider()
st.caption(t("Yeniden üretilebilirlik: tüm ekranlar aynı CSV sonuçlarından beslenir. Kaynaklar, ayarlar ve dosya özetleri manifest içinde saklanır.", "Reproducibility: all screens share the same CSV outputs. Sources, settings and file hashes are recorded in the manifest."))
