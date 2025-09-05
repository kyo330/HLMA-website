
import streamlit as st
from streamlit.components.v1 import html as st_html

st.set_page_config(page_title="Lightning — Fixed Area", layout="wide")
st.markdown("#### Lightning — Fixed Area (Emergency Response)")
st.caption("Interactive map with altitude-based coloring, clustering, heatmap, recent-strike filtering, wind markers, strike summary, and CSV download of filtered points.")

st_html('''<!DOCTYPE html>
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
    #map { flex:1; height: calc(100vh - 48px); position: relative; }
    fieldset { border:1px solid #e0e0e0; border-radius:8px; margin-bottom:12px; }
    legend { padding:0 6px; font-weight:600; }
    label { display:block; margin:8px 0 4px; font-size: 13px; }
    select, input[type="number"] { width:100%; }
    .row { display:flex; gap:8px; }
    .row > div { flex:1; }
    .summary {
      position: absolute; top: 16px; left: 16px; background: rgba(255,255,255,0.95);
      padding:10px; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.15); font-size:12px;
      min-width: 220px;
    }
    .summary h4 { margin: 0 0 6px 0; font-size: 13px; }
    .stat { display:flex; justify-content: space-between; margin: 2px 0; }
    .legend {
      position: absolute; bottom: 16px; left: 16px; background: rgba(255,255,255,0.95);
      padding:10px; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.15); font-size:12px;
    }
    .legend-item { display:flex; align-items:center; gap:8px; margin:4px 0; }
    .color-box { width: 16px; height: 16px; border-radius: 3px; }
    button { cursor:pointer; padding:8px 10px; border:1px solid #d0d0d0; background:#fafafa; border-radius:8px; }
    button:hover { background:#f0f0f0; }
    .footer-note { font-size: 11px; color:#666; margin-top:8px; }
    @media (max-width: 980px){
      #app { flex-direction: column; }
      #sidebar { width: auto; box-shadow: none; border-bottom:1px solid #eee; }
      #map { height: 70vh; }
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
        <span class="footer-note">Set 0 to ignore time filter. Looks for a column named <b>time</b> (ISO or epoch ms).</span>
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

  <script>
    // Map init (fixed area)
    var map = L.map('map').setView([30.7, -95.2], 8);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Layers
    let allMarkers = []; // {marker, alt, time?, lat, lon, tier}
    let clusterGroup = L.markerClusterGroup({ disableClusteringAtZoom: 12 });
    let plainGroup = L.layerGroup();
    let heatLayer = null;
    let windLayer = L.layerGroup().addTo(map);

    // Risk helpers
    function riskColor(alt){
      if (alt < 12000) return '#ffe633';
      if (alt < 14000) return '#ffc300';
      if (alt < 16000) return '#ff5733';
      return '#c70039';
    }
    function riskTier(alt){
      if (alt < 12000) return 'low';
      if (alt < 14000) return 'med';
      if (alt < 16000) return 'high';
      return 'extreme';
    }

    // Debounce util
    function debounce(fn, ms){
      let t; return function(){ clearTimeout(t); t = setTimeout(()=>fn.apply(this, arguments), ms); };
    }

    // CSV loaders
    function loadAltitudeCSV(){
      return new Promise((resolve, reject)=>{
        Papa.parse('https://raw.githubusercontent.com/kyo330/HLMA/main/filtered_LYLOUT_230924_210000_0600.csv', {
          download:true, header:true,
          complete: (res)=>resolve(res.data),
          error: reject
        });
      });
    }
    function loadWindCSV(){
      return new Promise((resolve, reject)=>{
        Papa.parse('https://raw.githubusercontent.com/kyo330/HLMA/main/230924_rpts_wind.csv', {
          download:true, header:true,
          complete: (res)=>resolve(res.data),
          error: reject
        });
      });
    }

    // Parse time if present
    function parseTime(val){
      if (!val) return null;
      if (!isNaN(val)) {
        const n = Number(val);
        if (n > 1e10) return new Date(n);
      }
      const d = new Date(val);
      return isNaN(d.getTime()) ? null : d;
    }

    // Build points
    function buildPoints(rows){
      allMarkers = [];
      (clusterGroup).clearLayers();
      (plainGroup).clearLayers();

      rows.forEach(r=>{
        const lat = parseFloat(r.lat);
        const lon = parseFloat(r.lon);
        const alt = parseFloat(r.alt);
        const t = parseTime(r.time); // optional

        if (isNaN(lat) || isNaN(lon) || isNaN(alt)) return;

        const color = riskColor(alt);
        const tier = riskTier(alt);
        const m = L.circleMarker([lat, lon], {
          radius: tier==='low'? 3 : tier==='med'? 5 : tier==='high'? 7 : 9,
          color, fillColor: color, fillOpacity: 0.85, opacity: 1, weight: 1
        }).bindPopup(`<b>Altitude:</b> ${alt} m<br><b>Tier:</b> ${tier.toUpperCase()}<br>` + (t? `<b>Time:</b> ${t.toISOString()}<br>`:'' ) + `(${lat.toFixed(3)}, ${lon.toFixed(3)})`);

        allMarkers.push({marker: m, alt, time: t, lat, lon, tier});
      });

      // default add to cluster
      allMarkers.forEach(o=>clusterGroup.addLayer(o.marker));
      clusterGroup.addTo(map);

      // Update total
      document.getElementById('sum-total').textContent = allMarkers.length;
    }

    // Wind markers (W icon)
    function buildWindMarkers(rows){
      windLayer.clearLayers();
      rows.forEach(r=>{
        const lat = parseFloat(r.Lat);
        const lon = parseFloat(r.Lon);
        const comments = r.Comments;
        if (isNaN(lat) || isNaN(lon)) return;
        const wind = L.marker([lat, lon], {
          icon: L.divIcon({
            className: 'wind-icon',
            html: '<span style="color:blue; font-weight:700; font-size:20px;">W</span>',
            iconSize: [24,24],
            iconAnchor: [12,12]
          })
        }).bindPopup(`<b>Wind Event:</b> ${comments || 'N/A'}<br>(${lat.toFixed(3)}, ${lon.toFixed(3)})`);
        wind.addTo(windLayer);
      });
    }

    // Filtering helpers
    function passAltitude(alt, range){
      if (range==='lt12') return alt < 12000;
      if (range==='12-14') return alt >= 12000 && alt < 14000;
      if (range==='14-16') return alt >= 14000 && alt < 16000;
      if (range==='gt16') return alt >= 16000;
      return true;
    }
    function passRecent(t, mins){
      if (!mins || mins<=0 || !t) return true;
      const now = new Date();
      const cutoff = new Date(now.getTime() - mins*60*1000);
      return t >= cutoff;
    }

    // Apply filters + update layers + summary
    function applyFilters(){
      const altRange = document.getElementById('altitude-filter').value;
      const cluster = document.getElementById('cluster-toggle').value === 'on';
      const heat = document.getElementById('heat-toggle').value === 'on';
      const mins = parseInt(document.getElementById('recent-mins').value || '0', 10);

      clusterGroup.clearLayers();
      plainGroup.clearLayers();
      if (heatLayer){ map.removeLayer(heatLayer); heatLayer = null; }

      const ptsForHeat = [];
      let visible = 0, cLow=0, cMed=0, cHigh=0, cExtreme=0;

      allMarkers.forEach(o=>{
        const ok = passAltitude(o.alt, altRange) && passRecent(o.time, mins);
        if (ok){
          visible++;
          if (o.tier==='low') cLow++; else if (o.tier==='med') cMed++; else if (o.tier==='high') cHigh++; else cExtreme++;
          if (cluster) clusterGroup.addLayer(o.marker);
          else plainGroup.addLayer(o.marker);
          ptsForHeat.push([o.lat, o.lon, 0.5 + Math.min(1, Math.max(0, (o.alt-10000)/8000)) ]);
        }
      });

      // attach correct layer
      if (cluster){
        if (!map.hasLayer(clusterGroup)) clusterGroup.addTo(map);
        if (map.hasLayer(plainGroup)) map.removeLayer(plainGroup);
      } else {
        if (!map.hasLayer(plainGroup)) plainGroup.addTo(map);
        if (map.hasLayer(clusterGroup)) map.removeLayer(clusterGroup);
      }

      // heat
      if (heat){
        heatLayer = L.heatLayer(ptsForHeat, { radius: 25, blur: 20, maxZoom: 11 });
        heatLayer.addTo(map);
      }

      // summary
      document.getElementById('sum-visible').textContent = visible;
      document.getElementById('sum-low').textContent = cLow;
      document.getElementById('sum-med').textContent = cMed;
      document.getElementById('sum-high').textContent = cHigh;
      document.getElementById('sum-extreme').textContent = cExtreme;
    }

    // CSV download of filtered points
    function downloadCSV(rows, filename) {
      const csvContent = rows.map(r => r.map(x => (typeof x === 'string' && x.includes(',')) ? ('"' + x.replace(/"/g,'""') + '"') : x).join(",")).join("\n");
      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }

    document.getElementById('download-points').addEventListener('click', ()=>{
      const altRange = document.getElementById('altitude-filter').value;
      const mins = parseInt(document.getElementById('recent-mins').value || '0', 10);

      const rows = [["lat","lon","altitude_m","tier","time_iso"]];
      allMarkers.forEach(o=>{
        if (passAltitude(o.alt, altRange) && passRecent(o.time, mins)) {
          rows.push([o.lat, o.lon, o.alt, o.tier, o.time? o.time.toISOString(): ""]);
        }
      });
      downloadCSV(rows, "filtered_points.csv");
    });

    // Wire UI
    document.getElementById('altitude-filter').addEventListener('change', debounce(applyFilters, 150));
    document.getElementById('cluster-toggle').addEventListener('change', applyFilters);
    document.getElementById('heat-toggle').addEventListener('change', applyFilters);
    document.getElementById('recent-mins').addEventListener('change', debounce(applyFilters, 150));

    // Load data
    Promise.all([loadAltitudeCSV(), loadWindCSV()]).then(([altRows, windRows])=>{
      buildPoints(altRows);
      buildWindMarkers(windRows);
      applyFilters();
    }).catch(err=>{
      console.error('Data load error:', err);
      alert('Failed to load data from GitHub CSV. Check network or URLs.');
    });
  </script>
</body>
</html>''', height=800, scrolling=True)
