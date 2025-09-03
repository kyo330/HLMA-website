# 3D Overshooting Explorer (Streamlit)

A streamlined Streamlit app to visualize overshooting points in 2D and 3D.

## Features
- CSV upload (or sample data)
- Map columns to `lat`, `lon`, `alt`, and an optional `is_overshooting`
- Filters for altitude range and overshooting-only
- Fast 2D scatter (lon vs lat) and 3D scatter (lon, lat, alt)
- Download filtered CSV

## How to run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Expected CSV columns
- **lat**: latitude (float)
- **lon**: longitude (float)
- **alt**: altitude (e.g., km)
- **is_overshooting** (optional): boolean or 0/1

If your column names differ, use the column mapping UI.
