# Logistics Data Quantification Dashboard

Static national supply chain coordinating unit dashboard for 2025 essential medicines reported vs adjusted consumption data.

## Contents

- `index.html` - dashboard shell
- `styles.css` - dashboard styling
- `app.js` - filters, charts, and table logic
- `data/dashboard-data.js` - generated reported/adjusted commodity consumption data
- `tools/extract_consumption_data.py` - rebuilds the data file from the source workbook

## Run Locally

Open `index.html` directly in a browser, or serve the folder with any static web server.

## Rebuild Data

```powershell
python tools/extract_consumption_data.py
```

The extraction script reads every named `Products Description` row as reported consumption. If the next row has a blank product description, that row is attached to the same commodity as adjusted consumption. Missing monthly values are treated as zero.
