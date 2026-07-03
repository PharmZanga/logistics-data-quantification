# Logistics Data Quantification Dashboard

Static national supply chain coordinating unit dashboard for essential medicines consumption data from 2024 to 2026, with available 2025 adjusted consumption and difference calculations.

## Contents

- `index.html` - dashboard shell
- `styles.css` - dashboard styling
- `app.js` - filters, charts, and table logic
- `data/dashboard-data.js` - generated commodity consumption, adjusted consumption, and difference data
- `tools/extract_consumption_data.py` - rebuilds the data file from the source workbook

## Run Locally

Open `index.html` directly in a browser, or serve the folder with any static web server.

## Rebuild Data

```powershell
python tools/extract_consumption_data.py
```

The extraction script reads every named `Products Description` row as one commodity row, keeps the wide month-column format from the workbook, and treats missing monthly consumption values as zero. It overlays 2025 adjusted consumption from `adjusted data EM 2025 consumption data.xlsx`; adjusted cells outside 2025 remain blank until those workbooks are available.
