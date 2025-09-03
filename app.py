
import streamlit as st
from streamlit.components.v1 import html as st_html

st.set_page_config(page_title="Leaflet + Wind Markers", layout="wide")
st.markdown("### Leaflet Map with Altitude-Based Filtering and Wind Markers")

# Render the provided HTML (loads Leaflet & PapaParse from CDN).
# Note: External JS/CSS are allowed in Streamlit components.
st_html("""<!DOCTYPE html>
<html lang="en">
<head>
    <title>Leaflet Map with Filtered Points and Wind Markers</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

    <!-- PapaParse for CSV Parsing -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.3.0/papaparse.min.js"></script>

   <style>
    #map {
        height: 600px;
        width: 800px;
        margin-top: 20px;
        position: relative; /* Added for relative positioning of the legend */
    }
    .filter-container {
        margin: 10px;
    }
    .legend {
        position: absolute;
        top: 100px;
        left: 830px; /* Placing it next to the map */
        background: white;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.15);
        width: 180px; /* Adjust width to fit content */
    }
    .legend-item {
        margin-bottom: 5px;
        display: flex;
        align-items: center;
    }
    .color-box {
        width: 20px;
        height: 20px;
        margin-right: 10px;
    }
</style>
</head>
<body>

<h3>Leaflet Map with Altitude-Based Filtering and Wind Markers</h3>

<div class="filter-container">
    <label for="altitude-filter">Select Altitude Range:</label>
    <select id="altitude-filter">
        <option value="all">All</option>
        <option value="lt12">Less than 12 km</option>
        <option value="12-14">12 - 14 km</option>
        <option value="14-16">14 - 16 km (Danger)</option>
        <option value="gt16">More than 16 km</option>
    </select>
</div>

<div id="map"></div>

<div class="legend">
    <h4>Altitude Legend</h4>
    <div class="legend-item"><span class="color-box" style="background:#ffe633;"></span> < 12 km</div>
    <div class="legend-item"><span class="color-box" style="background:#ffc300;"></span> 12 - 14 km</div>
    <div class="legend-item"><span class="color-box" style="background:#ff5733;"></span> 14 - 16 km</div>
    <div class="legend-item"><span class="color-box" style="background:#c70039;"></span> > 16 km</div>
   
</div>

<script>
    // Initialize the map centered over Texas
    var map = L.map('map').setView([30.7, -95.2], 10);

    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Store all markers globally to manage filtering
    let markers = [];
    let windMarkers = [];

    // Debounce utility function for smoother filtering
    function debounce(func, delay) {
        let timer;
        return function(...args) {
            clearTimeout(timer);
            timer = setTimeout(() => func.apply(this, args), delay);
        };
    }

    // Load all altitude data
    function loadAltitudeData() {
        Papa.parse('https://raw.githubusercontent.com/kyo330/HLMA/main/filtered_LYLOUT_230924_210000_0600.csv', {
            download: true,
            header: true,
            complete: function(results) {
                plotPoints(results.data);
            },
            error: function(error) {
                console.error('Error loading altitude CSV:', error);
            }
        });
    }

    // Load all wind data
    function loadWindData() {
        Papa.parse('https://raw.githubusercontent.com/kyo330/HLMA/main/230924_rpts_wind.csv', {
            download: true,
            header: true,
            complete: function(results) {
                plotWindMarkers(results.data);
            },
            error: function(error) {
                console.error('Error loading wind CSV:', error);
            }
        });
    }

    // Function to determine marker color based on altitude
    function getColor(alt) {
        if (alt < 12000) return '#fff600';
        else if (alt < 14000) return '#ff8f00';
        else if (alt < 16000) return '#ff0505'; // Danger range
        else return '#ff0505';
    }

    // Function to determine marker size based on altitude
    function getSize(alt) {
        if (alt < 12000) return 1;
        else if (alt < 14000) return 3;
        else if (alt < 16000) return 6;
        else return 9;
    }

    // Function to plot all altitude points
    function plotPoints(data) {
        data.forEach(function(row) {
            const lat = parseFloat(row.lat);
            const lon = parseFloat(row.lon);
            const alt = parseFloat(row.alt);

            if (!isNaN(lat) && !isNaN(lon) && !isNaN(alt)) {
                const marker = L.circleMarker([lat, lon], {
                    radius: getSize(alt),
                    color: getColor(alt),
                    opacity: 1,
                    fillOpacity: 0.8
                }).bindPopup(`<b>Altitude:</b> ${alt} meters<br>(${lat}, ${lon})`);

                markers.push({ marker, alt });
                marker.addTo(map);
            }
        });
    }

    // Function to plot all wind markers
    function plotWindMarkers(data) {
    data.forEach(function(row) {
        const lat = parseFloat(row.Lat);
        const lon = parseFloat(row.Lon);
        const comments = row.Comments;

        if (!isNaN(lat) && !isNaN(lon)) {
            const windMarker = L.marker([lat, lon], {
                icon: L.divIcon({
                    className: 'wind-icon',
                    html: '<span style="color:blue; font-weight: bold; font-size:24px;">W</span>', // Increased font size
                    iconSize: [30, 30], // Adjust icon size to ensure larger visual space
                    iconAnchor: [15, 15] // Center the marker on the correct lat-long
                })
            }).bindPopup(`<b>Wind Event:</b> ${comments}<br>(${lat}, ${lon})`);

            windMarkers.push(windMarker);
            windMarker.addTo(map);
        }
    });
}


    // Load both data sets immediately on page load
    loadAltitudeData();
    loadWindData();

    // Event listener for the filter dropdown with debounced filtering
    document.getElementById('altitude-filter').addEventListener('change', debounce(function(e) {
        filterMarkers(e.target.value);
    }, 200));

    // Filter markers based on altitude range and set non-matching markers to faint grey
    function filterMarkers(range) {
        markers.forEach(({ marker, alt }) => {
            const isVisible = {
                'lt12': alt < 12000,
                '12-14': alt >= 12000 && alt < 14000,
                '14-16': alt >= 14000 && alt < 16000,
                'gt16': alt >= 16000
            }[range] ?? true;

            if (isVisible) {
                // Highlight matching markers
                marker.setStyle({ fillOpacity: 0.8, color: getColor(alt), opacity: 1 });
            } else {
                // Faint grey for non-matching markers
                marker.setStyle({ fillOpacity: 0.05, color: 'grey', opacity: 0.05 });
            }
        });
    }

</script>

</body>
</html>
""", height=750, scrolling=True)
