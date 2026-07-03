import json
from datetime import datetime
from pathlib import Path

import pandas as pd


SOURCE = Path(r"C:\Users\Zanga Musakuzi\Downloads\EM CONSUMPTION DATA2024 TO 2026.xlsx")
OUTPUT = Path(__file__).resolve().parents[1] / "data" / "dashboard-data.js"
SHEET_NAME = "CONSUMPTION DATA"


def clean_text(value):
    if pd.isna(value):
        return ""
    return " ".join(str(value).strip().split())


def month_label(column):
    if isinstance(column, (datetime, pd.Timestamp)):
        # Workbook headers such as Jan-24 are exposed as 2026-01-24,
        # so the day is the year suffix and the month is still correct.
        return f"{column.strftime('%b')} {2000 + int(column.day)}"
    text = clean_text(column)
    if not text:
        return ""
    parsed = pd.to_datetime(text, errors="coerce")
    if not pd.isna(parsed):
        return month_label(parsed)
    return text


def month_value(row, column):
    value = pd.to_numeric(row.get(column), errors="coerce")
    if pd.isna(value):
        return 0
    return int(round(float(value)))


def main():
    df = pd.read_excel(SOURCE, sheet_name=SHEET_NAME)
    raw_rows = len(df)

    month_columns = []
    months = []
    for column in list(df.columns[2:]):
        label = month_label(column)
        if not label or label.lower().startswith("unnamed"):
            continue
        month_columns.append(column)
        months.append({"key": str(len(months)), "label": label})

    commodities = []
    blank_product_rows = 0
    for row_index, row in df.iterrows():
        product = clean_text(row.get("Products Description"))
        if not product:
            blank_product_rows += 1
            continue

        pack_size = clean_text(row.get("Pack Size")) or "Not specified"
        values = [month_value(row, column) for column in month_columns]
        monthly = [
            {
                "month": months[index]["label"],
                "value": value,
            }
            for index, value in enumerate(values)
        ]
        total = int(sum(values))
        highest_index = max(range(len(values)), key=lambda index: values[index]) if values else 0
        lowest_index = min(range(len(values)), key=lambda index: values[index]) if values else 0

        commodities.append(
            {
                "id": len(commodities) + 1,
                "sourceRow": int(row_index) + 2,
                "product": product,
                "packSize": pack_size,
                "values": values,
                "monthly": monthly,
                "total": total,
                "averageMonthly": round(total / len(values), 1) if values else 0,
                "activeMonths": int(sum(1 for value in values if value > 0)),
                "highestMonth": months[highest_index]["label"] if values else "",
                "highestValue": values[highest_index] if values else 0,
                "lowestMonth": months[lowest_index]["label"] if values else "",
                "lowestValue": values[lowest_index] if values else 0,
            }
        )

    totals_by_month = []
    for index, month in enumerate(months):
        totals_by_month.append(
            {
                "month": month["label"],
                "value": int(sum(item["values"][index] for item in commodities)),
            }
        )

    payload = {
        "source": {
            "fileName": SOURCE.name,
            "sheet": SHEET_NAME,
            "rawRows": raw_rows,
            "commodityRows": len(commodities),
            "blankProductRows": blank_product_rows,
            "generatedFrom": str(SOURCE),
            "period": f"{months[0]['label']} to {months[-1]['label']}" if months else "",
        },
        "months": [month["label"] for month in months],
        "totalsByMonth": totals_by_month,
        "commodities": commodities,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "window.NSCCU_DASHBOARD_DATA = "
        + json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT}")
    print(f"Commodity rows: {len(commodities):,}")
    print(f"Period: {payload['source']['period']}")


if __name__ == "__main__":
    main()
