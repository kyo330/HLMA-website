import streamlit as st
from streamlit.components.v1 import html as st_html

st.set_page_config(page_title="Lightning — Fixed Area", layout="wide")
st.markdown("#### Lightning — Fixed Area (Emergency Response)")
st.caption(
    "Map with altitude-based coloring, clustering, heatmap, recent-strike filtering, wind markers, "
    "strike summary, CSV download, and optional auto-refresh."
)

# Embed the HTML/JS Leaflet app
st_html(
    '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Lightning Map — Emergency Response (Fixed Area)</title>

  <!-- Leaflet -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

  <!-- Leaflet.markercluster -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
  <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>

  <!-- Leaflet.heat -->
  <script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>

  <!-- PapaParse -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.3.0/papaparse.min.js"></script>

  <style>
    :root { --sidebar-w: 320px; }
    html, body { height: 100%; }
    body { margin:0; font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }
    header { padding: 12px 16px; background:#0d47a1; color:white; }
    header h2 { margin: 0; font-size: 18px; }
    #app { display:flex; min-height: calc(100vh - 48px); }
    #sidebar {
      width: var(--sidebar-w);
      padding: 12px;
      box-shadow: 2px 0 6px rgba(0,0,0,0.08);
      z-index: 999;
      background: #fff;
    }
    #map { flex:1; width: 100%; height: 80vh; min-height: 600px; position: relative; }
    fieldset { border:1px solid #e0e0e0; border-radius:8px; margin-bottom:12px; }
    legend { padding:0 6px; font-weight:600; }
    label { display:block; margin:8px 0 4px; font-size: 13px; }
    select, input[type="number"] { width:100%; }
    .row { display:flex; gap:8px; }
    .row > div { flex:1; }
    .summary {
      position: absolute; top: 16px; left: 16px; background: rgba(255,255,255,0.95);
      padding:10px; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.15); font-size:12px;
      min-width: 220px; z-index: 500;
    }
    .summary h4 { margin: 0 0 6px 0; font-size: 13px; }
    .stat { display:flex; justify-content: space-between; margin: 2px 0; }
    .legend {
      position: absolute; bottom: 16px; left: 16px; background: rgba(255,255,255,0.95);
      padding:10px; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.15); font-size:12px;
      z-index: 500;
    }
    .legend-item { display:flex; align-items:center; gap:8px; margin:4px 0; }
    .color-box { width: 16px; height: 16px; border-radius: 3px; }
    button { cursor:pointer; padding:8px 10px; border:1px solid #d0d0d0; background:#fafafa; border-radius:8px; }
    button:hover { background:#f0f0f0; }
    .footer-note { font-size: 11px; color:#666; margin-top:8px; }
    @media (max-width: 980px){
      #app { flex-direction: column; }
      #sidebar { width: auto; box-shadow: none; border-bottom:1px solid #eee; }
      #map { height: 70vh; min-height: 420px; }
      .summary { position: static; margin: 8px; }
    }
  </style>
</head>
<body>
  <header>
    <h2>Lightning — Fixed Area (Emergency Response)</h2>
  </header>

  <div id="app">
    <aside id="sidebar">
      <fieldset>
        <legend>Filters</legend>
        <label for="altitude-filter">Altitude range</label>
        <select id="altitude-filter">
          <option value="all">All</option>
          <option value="lt12">&lt; 12 km</option>
          <option value="12-14">12–14 km</option>
          <option value="14-16">14–16 km (Danger)</option>
          <option value="gt16">&gt; 16 km</option>
        </select>

        <div class="row">
          <div>
            <label for="cluster-toggle">Marker clustering</label>
            <select id="cluster-toggle">
              <option value="on">On</option>
              <option value="off">Off</option>
            </select>
          </div>
          <div>
            <label for="heat-toggle">Heatmap</label>
            <select id="heat-toggle">
              <option value="off">Off</option>
              <option value="on">On</option>
            </select>
          </div>
        </div>

        <label for="recent-mins">Show strikes from last (minutes)</label>
        <input type="number" id="recent-mins" min="0" step="5" value="0" />

        <fieldset>
          <legend>Auto-refresh</legend>
          <div class="row">
            <div>
              <label for="auto-refresh">Enable</label>
              <select id="auto-refresh">
                <option value="off">Off</option>
                <option value="on">On</option>
              </select>
            </div>
            <div>
              <label for="refresh-sec">Every (seconds)</label>
              <input type="number" id="refresh-sec" min="30" step="30" value="120" />
            </div>
          </div>
          <div class="footer-note" id="refresh-note">Auto-refresh is off.</div>
        </fieldset>

        <fieldset>
          <legend>Downloads</legend>
          <button id="download-points">Download filtered points (CSV)</button>
        </fieldset>

        <div class="footer-note">
          Data pulled via CSV from GitHub; tiles © OpenStreetMap. Use for awareness; confirm with official guidance.
        </div>
      </aside>

      <div id="map">
        <div class="summary" id="summary">
          <h4>Strike Summary</h4>
          <div class="stat"><span>Total (all data):</span><strong id="sum-total">0</strong></div>
          <div class="stat"><span>Visible (filters):</span><strong id="sum-visible">0</strong></div>
          <hr>
          <div class="stat"><span>&lt; 12 km:</span><strong id="sum-low">0</strong></div>
          <div class="stat"><span>12–14 km:</span><strong id="sum-med">0</strong></div>
          <div class="stat"><span>14–16 km:</span><strong id="sum-high">0</strong></div>
          <div class="stat"><span>&gt; 16 km:</span><strong id="sum-extreme">0</strong></div>
        </div>
      </div>
    </div>

    <div class="legend" id="legend">
      <div class="legend-item"><span class="color-box" style="background:#ffe633;"></span> &lt; 12 km (Low)</div>
      <div class="legend-item"><span class="color-box" style="background:#ffc300;"></span> 12–14 km (Medium)</div>
      <div class="legend-item"><span class="color-box" style="background:#ff5733;"></span> 14–16 km (High / Danger)</div>
      <div class="legend-item"><span class="color-box" style="background:#c70039;"></span> &gt; 16 km (Extreme)</div>
    </div>
</body>
</html>''',
    height=900,
    scrolling=True
)
