
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="3D Overshooting Explorer", layout="wide")

st.title("3D Overshooting Explorer")
st.write("Upload a CSV and explore 2D and 3D visualizations.")

# Sidebar: File upload or sample
with st.sidebar:
    st.header("Data")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    use_sample = st.checkbox("Use sample data", value=uploaded is None)
    st.caption("Your CSV should include latitude, longitude, altitude, and (optionally) a boolean flag like `is_overshooting`.")

def make_sample(n=500, seed=7):
    rng = np.random.default_rng(seed)
    lat = 25 + 20 * rng.random(n)     # 25..45
    lon = -105 + 20 * rng.random(n)   # -105..-85
    alt = 5 * rng.random(n)           # 0..5 km
    is_over = rng.random(n) > 0.8
    return pd.DataFrame({"lat": lat, "lon": lon, "alt": alt, "is_overshooting": is_over})

# Load data
if use_sample:
    df = make_sample()
else:
    if uploaded is None:
        st.stop()
    try:
        df = pd.read_csv(uploaded)
    except Exception as e:
        st.error(f"Could not read CSV: {e}")
        st.stop()

st.subheader("Column Mapping")
# Infer likely columns
def guess(colnames, keys):
    low = {c.lower(): c for c in colnames}
    return [low.get(k) for k in keys]

colnames = list(df.columns)
lat_guess, lon_guess, alt_guess, over_guess = guess(colnames, ["lat", "lon", "alt", "is_overshooting"])

c1, c2, c3, c4 = st.columns(4)
lat_col = c1.selectbox("Latitude", options=["<None>"] + colnames, index=(colnames.index(lat_guess) + 1) if lat_guess in colnames else 0)
lon_col = c2.selectbox("Longitude", options=["<None>"] + colnames, index=(colnames.index(lon_guess) + 1) if lon_guess in colnames else 0)
alt_col = c3.selectbox("Altitude", options=["<None>"] + colnames, index=(colnames.index(alt_guess) + 1) if alt_guess in colnames else 0)
over_col = c4.selectbox("Overshooting flag (optional)", options=["<None>"] + colnames, index=(colnames.index(over_guess) + 1) if over_guess in colnames else 0)

required_missing = [x for x in [lat_col, lon_col, alt_col] if x == "<None>"]
if required_missing:
    st.warning("Please map Latitude, Longitude, and Altitude columns to continue.")
    st.stop()

# Normalize columns
work = df.copy()
work = work.rename(columns={lat_col: "_lat", lon_col: "_lon", alt_col: "_alt"})
if over_col != "<None>":
    work = work.rename(columns={over_col: "_over"})
else:
    work["_over"] = False

# Coerce types
for k in ["_lat", "_lon", "_alt"]:
    work[k] = pd.to_numeric(work[k], errors="coerce")
work = work.dropna(subset=["_lat", "_lon", "_alt"])

st.subheader("Filters")
c5, c6, c7 = st.columns(3)
alt_min, alt_max = float(np.nanmin(work["_alt"])), float(np.nanmax(work["_alt"]))
alt_sel = c5.slider("Altitude range", min_value=0.0, max_value=max(alt_max, 1.0), value=(alt_min, alt_max))
over_only = c6.checkbox("Show overshooting only", value=False)
sample_n = c7.number_input("Downsample (rows)", min_value=100, max_value=len(work), value=min(2000, len(work)))

filt = (work["_alt"].between(alt_sel[0], alt_sel[1]))
if over_only:
    filt &= work["_over"].astype(bool)

work_f = work.loc[filt].copy()
if len(work_f) > sample_n:
    work_f = work_f.sample(int(sample_n), random_state=42)

st.caption(f"Showing {len(work_f):,} points (of {len(work):,} total after cleaning).")

# Two columns for charts
left, right = st.columns(2)

with left:
    st.markdown("### 2D Scatter (Lon vs Lat)")
    color = np.where(work_f["_over"], "Overshooting", "Normal")
    fig2d = go.Figure()
    fig2d.add_trace(go.Scattergl(
        x=work_f["_lon"], y=work_f["_lat"],
        mode="markers",
        text=[f"Alt: {a:.2f}" for a in work_f["_alt"]],
        marker=dict(size=5),
        name="Points"
    ))
    fig2d.update_layout(
        xaxis_title="Longitude",
        yaxis_title="Latitude",
        height=500
    )
    st.plotly_chart(fig2d, use_container_width=True)

with right:
    st.markdown("### 3D Scatter (Lon, Lat, Alt)")
    colors = np.where(work_f["_over"], "#d62728", "#1f77b4")
    fig3d = go.Figure(data=[go.Scatter3d(
        x=work_f["_lon"], y=work_f["_lat"], z=work_f["_alt"],
        mode="markers",
        marker=dict(size=3, color=colors),
        text=[f"Alt: {a:.2f}" for a in work_f["_alt"]],
        hoverinfo="text"
    )])
    fig3d.update_layout(
        scene=dict(
            xaxis_title="Longitude",
            yaxis_title="Latitude",
            zaxis_title="Altitude"
        ),
        height=500
    )
    st.plotly_chart(fig3d, use_container_width=True)

st.subheader("Data Preview")
st.dataframe(work_f.rename(columns={"_lat":"lat","_lon":"lon","_alt":"alt","_over":"is_overshooting"}))

st.download_button(
    "Download filtered CSV",
    work_f.to_csv(index=False).encode("utf-8"),
    file_name="filtered.csv",
    mime="text/csv"
)

st.info("Tip: deploy on Streamlit Community Cloud or run locally with `streamlit run app.py`.")
