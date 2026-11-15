import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="HydroGeoPulse", layout="wide")
OUT = "outputs"

# ---------------- theme ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap');
h1, h2, h3, h4 { font-family:'Montserrat', sans-serif !important; font-weight:700; letter-spacing:.3px; }[data-testid="stIconMaterial"], [class*="material-symbols"] { font-family:'Material Symbols Rounded' !important; }
.block-container { padding-top: 1.5rem; }
[data-testid="stMetric"]{ background:#f5e2c8; border:1px solid #e6d5b8; border-radius:16px; padding:18px 22px; }
[data-testid="stSidebar"]{ min-width:380px; max-width:380px; }
</style>
""", unsafe_allow_html=True)

# ---------------- data ----------------
@st.cache_data
def load_summary():
    return pd.read_csv(f"{OUT}/summary.csv")

@st.cache_data
def load_basin(slug):
    df = pd.read_csv(f"{OUT}/basins/{slug}.csv", parse_dates=["date"])
    for c in ["flag_2sigma", "flag_mad", "flag_if"]:
        df[c] = df[c].astype(str).str.strip().str.lower().eq("true")
    return df

summary = load_summary()

def legend(items):
    st.markdown(" &nbsp;&nbsp; ".join(
        f"<span style='display:inline-block;width:11px;height:11px;border-radius:50%;"
        f"background:{c};margin-right:6px;vertical-align:middle'></span>"
        f"<span style='font-size:.9rem'>{l}</span>" for c, l in items),
        unsafe_allow_html=True)

# basin -> (lat, lon, zoom) for globe centering
BASINS = {"🌍 Global View": (0.0, 0.0, 1.0)}
for _, r in summary.iterrows():
    BASINS[r["Basin"]] = (float(r["lat"]), float(r["lon"]), 2.4)

INTERP = {
 "Ganges (N India)": {
    "simple": "People pump out groundwater for farming faster than the rain refills it, so the water underground is slowly running out ; about a 1 cm layer lost every year across the whole region. This leads to a serious water supply issue for the hundreds of millions who live here.",
   "technical": "Anthropogenic abstraction across the Indo-Gangetic aquifer exceeds monsoonal recharge → secular TWS decline of ~1.07 cm/yr, significant under autocorrelation-corrected Mann-Kendall (p≈4e-11)."},
 "North China Plain": {
   "simple": "One of the most over-used underground water supplies on Earth. Decades of farming and city use have drained it, so much that it's part of why China built a giant canal to move water up from the south.",
   "technical": "Chronic aquifer depletion from agricultural/municipal extraction; the negative TWS trend is consistent with deficits motivating the South-to-North Water Diversion."},
 "California C. Valley": {
   "simple": "Farms pump groundwater here too. Something cool: removing all that heavy water lets the ground spring slowly upward. Like a sponge rising when you squeeze it, and that tiny rise even changes the pressure on the San Andreas fault. The pumping also makes the valley floor itself sink.",
   "technical": "Agricultural depletion; unloading drives elastic crustal uplift of the Sierra Nevada and modulates San Andreas stress (Amos et al., Nature 2014); poroelastic compaction causes InSAR-observable subsidence."},
 "Amazon (control)": {
   "simple": "Water swings way up and down each year with the seasons, but over the long run it's not really trending either way. It's our 'nothing's changing' check, and the tool correctly says so.",
   "technical": "Control basin dominated by seasonal/interannual variability, no significant secular trend (p=0.18); validates detector specificity."},
 "Zambezi / Okavango (S Africa)": {
   "simple": "No real long-term up or down, just natural ups and downs. A second 'nothing's changing' we have found!",
   "technical": "No significant long-term trend; interannual hydroclimatic variability dominates. Secondary control."},
 "Great Lakes (N America)": {
   "simple": "Leans slightly toward gaining water, but not enough to be sure it's real, could just be luck. A reminder that 'looks like it's rising' isn't the same as 'definitely rising'.",
   "technical": "Weakly positive, non-significant after correction (p_fdr≈0.15); illustrates apparent vs significant trends."},
 "NW Australia": {
   "simple": "Often called a 'getting wetter' spot, but our strict test says the rise isn't quite certain enough to count. Reported honestly as 'no clear trend'.",
   "technical": "Reported wetting region; fails significance under the conservative corrected test (p≈0.09). Reported as null."},
 "East Africa Lakes": {
   "simple": "Here water is clearly going UP. The big African lakes rose to record highs around 2019-2020 after huge rains. Nature adding water, the opposite of the human draining happening elsewhere.",
   "technical": "Significant positive trend (+1.63 cm/yr, p≈1e-5), driven by anomalous 2019-2020 East African rainfall, a climate-forced gain contrasting anthropogenic depletion."},
}

# ---------------- sidebar ----------------
if "basin" not in st.session_state:
    st.session_state.basin = "🌍 Global View"

names = list(BASINS)
if "basin" not in st.session_state:
    st.session_state.basin = "🌍 Global View"

st.sidebar.markdown("<div style='font-size:1.2rem;font-weight:700;margin:4px 0 8px'>🌊 Choose a region</div>",
                    unsafe_allow_html=True)
for name in names:
    is_sel = name == st.session_state.basin
    if st.sidebar.button(name, key=f"b_{name}", use_container_width=True,
                         type="primary" if is_sel else "secondary"):
        st.session_state.basin = name
        st.rerun()

basin = st.session_state.basin

mode = st.sidebar.radio("Explain for:", ["🧑‍🎓 The Curious", "🔬 The Scientist"])
key = "technical" if mode.startswith("🔬") else "simple"

with st.sidebar.expander("What am I looking at?"):
    st.write("NASA satellites weigh how much water each region stores: in soil, snow, lakes, and underground. We track whether a place is gaining or losing water over ~24 years, and check whether the change is real or just random wobble."
             if key == "simple" else
             "GRACE/GRACE-FO measure time-variable gravity → terrestrial water-storage anomalies (cm equiv. water height). Secular trends via Theil-Sen + Hamed-Rao-corrected Mann-Kendall; block-bootstrap CIs; Benjamini-Hochberg FDR control.")

with st.sidebar.expander("Why does this matter?"):
    st.write("Water is life. When a region quietly loses its groundwater year after year, it threatens the food and drinking water of the people who live there. The shifting water mass can even make the land rise or sink. This tool spots those changes early and proves they're real."
             if key == "simple" else
             "Terrestrial water storage integrates climate forcing, human extraction, and the solid-Earth response. Robust, validated trend detection underpins water-security assessment, drought monitoring, and GRACE-informed studies of crustal loading, uplift, and subsidence.")
    
# ---------------- header ----------------
st.title("HydroGeoPulse")
st.caption("NASA Space Apps Challenge 2026 · Where is Earth gaining or losing water, is the change real? Built from NASA satellite measurements."
           if key == "simple" else
           "NASA Space Apps Challenge 2026 · Detecting and statistically validating terrestrial water-storage trends from NASA GRACE / GRACE-FO.")

# ---------------- 3D globe ----------------
clat, clon, czoom = BASINS[basin]
globe = go.Figure(go.Scattergeo(
    lon=summary["lon"], lat=summary["lat"], customdata=summary["Basin"],
    mode="markers", hovertext=summary["Basin"], hoverinfo="text",
    marker=dict(size=np.clip(summary["slope_cm_yr"].abs()*9+9, 9, 30),
                color=summary["slope_cm_yr"], colorscale="RdBu_r",
                cmin=-1.7, cmax=1.7, line=dict(width=1.2, color="#2C1E16"),
                colorbar=dict(title="cm/yr", outlinewidth=0)),
))
globe.update_geos(
    projection_type="orthographic",
    projection_rotation=dict(lon=clon, lat=clat, roll=0),
    projection_scale=czoom,
    showocean=True, oceancolor="#2B5B84",      # the blue sphere (the "sea")
    showland=True, landcolor="#FAF4E8",        # the continents (light cream)
    showlakes=True, lakecolor="#2B5B84",
    showcountries=True, countrycolor="#e3d9c3",
    showcoastlines=True, coastlinecolor="#d8ccb2",
    showframe=False,
    bgcolor="rgba(0,0,0,0)",                   # area BEHIND the sphere (shows page cream)
)
globe.update_layout(height=520, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)")

ev = st.plotly_chart(globe, use_container_width=True, on_select="rerun", selection_mode="points", key="globe")
pts = (ev or {}).get("selection", {}).get("points", []) if hasattr(ev, "get") else []
if pts:
    cd = pts[0].get("customdata")
    clicked = cd[0] if isinstance(cd, (list, tuple)) else cd
    if clicked and clicked != basin:
        st.session_state.basin = clicked
        st.rerun()

st.caption("Drag to spin the globe • pick a basin from the sidebar or click a dot")
legend([("#b2182b", "losing water"), ("#2166ac", "gaining water")])

def styled(f):
    f.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#2C1E16", family="Plus Jakarta Sans"),
                    margin=dict(t=10), showlegend=False)
    for ax in (f.update_xaxes, f.update_yaxes):
        ax(gridcolor="rgba(0,0,0,0.25)", linecolor="#2C1E16",
           tickcolor="#2C1E16", tickfont=dict(color="#2C1E16"), zeroline=False)
    return f

def legend(items):
    st.markdown(" &nbsp;&nbsp; ".join(
        f"<span style='display:inline-block;width:11px;height:11px;border-radius:50%;"
        f"background:{c};margin-right:6px;vertical-align:middle'></span>"
        f"<span style='font-size:.9rem'>{l}</span>" for c, l in items),
        unsafe_allow_html=True)

# ---------------- global view vs basin detail ----------------
if basin == "🌍 Global View":
    st.subheader("All basins at a glance")
    st.markdown("""
    <style>
    .glance{width:100%;border-collapse:collapse;font-size:1.05rem;color:#2C1E16;margin-top:6px}
    .glance th{padding:13px 18px;text-align:center;font-weight:600;background:#f5e2c8;border-bottom:2px solid #e0cfae}
    .glance td{padding:12px 18px;text-align:center;border-bottom:1px solid #ecdcc0}
    .glance tbody tr:hover{background:#faf0d8}
    </style>
    """, unsafe_allow_html=True)

    def trend_cell(t):
        if t == "decreasing": return ("Losing water" if key == "simple" else "decreasing"), "#b2182b"
        if t == "increasing": return ("Gaining water" if key == "simple" else "increasing"), "#2166ac"
        return ("No clear change" if key == "simple" else "no trend"), "#8a7a64"

    heads = (["Region", "Change (cm/yr)", "What's happening", "Likely range"] if key == "simple"
             else ["Basin", "Slope (cm/yr)", "Trend", "95% CI"])
    body = ""
    for _, r in summary.iterrows():
        lab, col = trend_cell(r["trend"])
        body += (f"<tr><td style='font-weight:600'>{r['Basin']}</td>"
                 f"<td>{r['slope_cm_yr']:+.2f}</td>"
                 f"<td style='color:{col};font-weight:700'>{lab}</td>"
                 f"<td>[{r['CI_low']:.2f}, {r['CI_high']:.2f}]</td></tr>")
    th = "".join(f"<th>{h}</th>" for h in heads)
    st.markdown(f"<table class='glance'><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>",
                unsafe_allow_html=True)
    st.info("Pick a basin from the sidebar/ or click a dot on the globe to dive into one region." if key == "simple"
            else "Select a basin to inspect its trend decomposition, significance, and anomaly analysis.")
else:
    row = summary[summary["Basin"] == basin].iloc[0]
    df = load_basin(row["slug"])
    sig = str(row["significant_fdr"]).strip().lower() == "true"

    st.markdown(f"## {basin}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Rate of change" if key == "simple" else "Trend", f"{row['slope_cm_yr']:+.2f} cm/yr")
    c2.metric("Likely range" if key == "simple" else "95% CI", f"[{row['CI_low']:.2f}, {row['CI_high']:.2f}]")
    c3.metric("Verdict", ("Real change" if sig else "Not sure it's real") if key == "simple"
              else ("Significant" if sig else "No significant trend"))
    st.info(INTERP.get(basin, {}).get(key, ""))

    TABS = (["Water over time", "Yearly cycle", "Unusual months", "How it works"] if key == "simple"
            else ["Trend", "Seasonality", "Anomalies", "Methodology"])
    t1, t2, t3, t4 = st.tabs(TABS)

    with t1:
        f = go.Figure()
        f.add_scatter(x=df["date"], y=df["raw"], name="water level" if key == "simple" else "water storage", line=dict(color="#9a8c74", width=1))
        f.add_scatter(x=df["date"], y=df["raw"] - df["residual"], name="fitted pattern" if key == "simple" else "trend + season fit", line=dict(color="#2B5B84"))
        f.update_layout(height=360, yaxis_title="water level (cm)" if key == "simple" else "cm equiv. water")
        st.plotly_chart(styled(f), use_container_width=True)
        legend([("#9a8c74", "actual water level each month"), ("#2B5B84", "fitted pattern")])

    with t2:
        f = go.Figure()
        f.add_scatter(x=df["date"], y=df["deseasonalized"], name="yearly cycle removed" if key == "simple" else "deseasonalized", line=dict(color="#2e7d52"))
        f.add_scatter(x=df["date"], y=df["trend_line"], name="long-term direction" if key == "simple" else "trend", line=dict(color="#2C1E16", dash="dash"))
        f.update_layout(height=360, yaxis_title="water level, cycle removed (cm)" if key == "simple" else "cm (season removed)")
        st.plotly_chart(styled(f), use_container_width=True)
        legend([("#2e7d52", "yearly cycle removed"), ("#2C1E16", "long-term direction")])

    with t3:
        labels = ({"flag_mad": "Careful (rarely false-alarms)", "flag_2sigma": "Sensitive (catches more)", "flag_if": "AI model that detects sudden changes"}
                  if key == "simple" else
                  {"flag_mad": "MAD (robust, high precision)", "flag_2sigma": "2σ (high recall)", "flag_if": "Isolation Forest (ML)"})
        method = st.radio("How picky should the detector be?" if key == "simple" else "Anomaly method",
                          ["flag_mad", "flag_2sigma", "flag_if"], format_func=lambda x: labels[x], horizontal=True)
        f = go.Figure()
        f.add_scatter(x=df["date"], y=df["residual"], name="surprise" if key == "simple" else "residual", line=dict(color="#b8ad94", width=1))
        hit = df[df[method]]
        f.add_scatter(x=hit["date"], y=hit["residual"], mode="markers", name="unusual month" if key == "simple" else "anomaly", marker=dict(color="#c0392b", size=9))
        f.update_layout(height=360, yaxis_title="how surprising (cm)" if key == "simple" else "residual (cm)")
        st.plotly_chart(styled(f), use_container_width=True)
        st.caption(f"{int(df[method].sum())} unusually wet or dry months — surprises left after removing the yearly pattern and the slow trend. Could be droughts or floods, but we'd need rainfall data to be sure."
                   if key == "simple" else
                   f"{int(df[method].sum())} residual outliers after removing trend + seasonality; candidate extremes — verify against independent records before attributing cause.")
        legend([("#b8ad94", "monthly surprise"), ("#c0392b", "flagged unusual month")])

    with t4:
        if key == "simple":
            st.markdown("""
**How this works, step by step:**
1. NASA satellites measure how much water each region holds, every month, for ~24 years.
2. We strip out the normal yearly wet/dry cycle, so the slow change underneath becomes visible.
3. We measure how fast water is rising or falling, in cm per year.
4. We check whether that change is **real or just random luck**! And we tested our own check with fake data to make sure it doesn't cry wolf.
5. We put an honest "could be anywhere from X to Y" range on every number.

**Keep in mind:** the satellites see big areas, not small ones, so tiny regions look blurry. We look for straight-line changes. An "unusual month" is just a statistical surprise, we'd need rainfall data to call it a real drought.
""")
        else:
            st.markdown("""
**Pipeline:** GRACE/GRACE-FO mascon water storage → basin area-average (cos-lat weighted)
→ remove seasonal cycle (harmonic regression) → trend magnitude (Theil–Sen)
→ significance (Mann–Kendall + Hamed–Rao autocorrelation correction)
→ precision (block-bootstrap 95% CI) → multiple-testing control (Benjamini–Hochberg).

**Validation:** Monte-Carlo false-alarm calibration; synthetic-injection benchmark of three anomaly detectors (2σ / MAD / Isolation Forest).

**Limitations:** GRACE resolution ~300 km → small basins leak. Linear trends; 2017–18 gap treated as missing. Anomalies are statistical, cause needs independent data (GPM rainfall).
""")

st.markdown("---")
with st.expander("🌍 Why this matters: water and the solid Earth", expanded=False):
    st.markdown("""
    <svg viewBox="0 0 560 130" style="width:100%;max-width:560px;display:block;margin:4px auto">
      <rect x="30" y="50" width="190" height="28" rx="4" fill="#2B5B84"/>
      <path d="M30,86 Q125,114 220,86" stroke="#9a6b3a" stroke-width="7" fill="none" stroke-linecap="round"/>
      <text x="125" y="36" text-anchor="middle" fill="#2C1E16" font-size="13" font-weight="600">more water → crust bends down</text>
      <text x="125" y="115" text-anchor="middle" fill="#b2182b" font-size="11">downward flex</text>
      <path d="M340,86 Q435,60 530,86" stroke="#9a6b3a" stroke-width="7" fill="none" stroke-linecap="round"/>
      <text x="435" y="36" text-anchor="middle" fill="#2C1E16" font-size="13" font-weight="600">less water → crust springs up</text>
      <text x="435" y="90" text-anchor="middle" fill="#2166ac" font-size="11">uplift</text>
    </svg>
    """, unsafe_allow_html=True)

    st.markdown(
    "Water is heavy. When a place holds a lot of water, all that weight pushes down on the ground, "
    "like sitting on a mattress. When the water leaves, the ground slowly springs back up, just a tiny "
    "bit (a few millimetres). So the changes this tool finds aren't only about water, they actually make "
    "the land **rise and sink**. Near the Ganges, scientists have watched this happen with GPS: the ground "
    "gently rises and drops every year as the monsoon rains come and go."
    if key == "simple" else
    "GRACE-observed terrestrial water storage is a surface **mass load**; its variation drives **elastic "
    "crustal deformation** (mm-scale vertical displacement) measurable by GNSS. Our detected trends are the "
    "loading signal. Independent GNSS studies in the Ganges-Brahmaputra (Materna et al. 2021) resolve the "
    "corresponding vertical displacement, with GRACE-based loading models explaining much of the seasonal signal.")

    st.markdown(
        "**What we did vs what scientists already proved:** our tool spots and double-checks where water is being "
        "lost or gained, that's the **cause**. Other scientists have used GPS to measure the ground actually "
        "moving up and down because of that water, that's the **effect** in the very same part of the world. "
        "We don't measure the ground movement ourselves; we find and prove the water change that drives it, and "
        "point to the published research that shows the rest."
        if key == "simple" else
        "**What HydroGeoPulse measured vs what research has shown:** we detect and statistically validate the "
        "water-mass *trends* — the **cause**. Published geodetic studies measure the crustal *displacement* those "
        "loads produce — the **effect** — in this same South Asian region. We do not compute deformation here; we "
        "identify and verify the load that drives it, and point to the peer-reviewed work that closes the loop.")

    st.markdown(
        ("**Research behind this**  \n"
         "• **Materna et al. (2021)** — confirmed that seasonal water loss makes Earth's crust rise across South & Southeast Asia, including the Ganges region.  \n"
         "• **White et al. (2022)** — showed how GPS can be used to measure water storage and drought.  \n"
         "• **Heki & Jin (2023)** — explained the simple cause-and-effect: heavy stuff sitting on Earth, and how much the ground squishes under that weight.")
        if key == "simple" else
        ("**References**  \n"
         "• Materna et al. (2021), *Geophysical Journal International* — GNSS characterization of hydrological loading in South & Southeast Asia  \n"
         "• White et al. (2022), *Water Resources Research* — A Review of GNSS/GPS in Hydrogeodesy  \n"
         "• Heki & Jin (2023), *Satellite Navigation* — Geodetic study on earth surface loading with GNSS and GRACE"))