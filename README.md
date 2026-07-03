# Logistics Data Quantification Dashboard

Static national supply chain coordinating unit dashboard for 2025 essential medicines consumption data.

## Contents

- `index.html` - dashboard shell
- `styles.css` - dashboard styling
- `app.js` - filters, charts, and table logic
- `data/dashboard-data.js` - generated commodity consumption data
- `tools/extract_consumption_data.py` - rebuilds the data file from the source workbook

## Run Locally

Open `index.html` directly in a browser, or serve the folder with any static web server.

## Rebuild Data

```powershell
python tools/extract_consumption_data.py
```

The extraction script aggregates named rows by `Products Description + Pack Size`, sums monthly consumption, and preserves data quality counts for blank commodity rows.
