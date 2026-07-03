import json
from datetime import datetime
from pathlib import Path

import pandas as pd


SOURCE = Path(r"C:\Users\Zanga Musakuzi\Downloads\EM CONSUMPTION DATA2024 TO 2026.xlsx")
ADJUSTED_SOURCE = Path(r"C:\Users\Zanga Musakuzi\Desktop\adjusted data EM 2025 consumption data.xlsx")
OUTPUT = Path(__file__).resolve().parents[1] / "data" / "dashboard-data.js"
SHEET_NAME = "CONSUMPTION DATA"
ADJUSTED_SHEET_NAME = "Sheet1"
ADJUSTED_MONTHS = [
    ("JAN", "Jan 2025"),
    ("FEB", "Feb 2025"),
    ("MAR", "Mar 2025"),
    ("APR", "Apr 2025"),
    ("MAY", "May 2025"),
    ("JUN", "Jun 2025"),
    ("JUL", "Jul 2025"),
    ("AUG", "Aug 2025"),
    ("SEP", "Sep 2025"),
    ("OCT", "Oct 2025"),
    ("NOVE", "Nov 2025"),
    ("DEC", "Dec 2025"),
]


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


def commodity_key(product, pack_size):
    return f"{clean_text(product).lower()}||{clean_text(pack_size).lower()}"


def load_adjusted_2025():
    adjusted_df = pd.read_excel(ADJUSTED_SOURCE, sheet_name=ADJUSTED_SHEET_NAME)
    adjusted_map = {}
    adjusted_pairs = 0

    index = 0
    while index < len(adjusted_df):
        row = adjusted_df.iloc[index]
        product = clean_text(row.get("Products Description"))
        if not product:
            index += 1
            continue

        pack_size = clean_text(row.get("Pack Size")) or "Not specified"
        adjusted_row = None
        if index + 1 < len(adjusted_df):
            next_row = adjusted_df.iloc[index + 1]
            if not clean_text(next_row.get("Products Description")):
                adjusted_row = next_row
                adjusted_pairs += 1

        if adjusted_row is not None:
            adjusted_map[commodity_key(product, pack_size)] = {
                label: month_value(adjusted_row, column) for column, label in ADJUSTED_MONTHS
            }

        index += 2 if adjusted_row is not None else 1

    return adjusted_map, adjusted_pairs


def load_existing_consumption_payload():
    if not OUTPUT.exists():
        return None
    text = OUTPUT.read_text(encoding="utf-8")
    prefix = "window.NSCCU_DASHBOARD_DATA = "
    if not text.startswith(prefix):
        return None
    return json.loads(text[len(prefix) :].rstrip(";\n"))


def main():
    adjusted_map, adjusted_pairs = load_adjusted_2025()
    existing_payload = None

    if SOURCE.exists():
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

        source_rows = []
        blank_product_rows = 0
        for row_index, row in df.iterrows():
            product = clean_text(row.get("Products Description"))
            if not product:
                blank_product_rows += 1
                continue
            source_rows.append(
                {
                    "sourceRow": int(row_index) + 2,
                    "product": product,
                    "packSize": clean_text(row.get("Pack Size")) or "Not specified",
                    "values": [month_value(row, column) for column in month_columns],
                }
            )
        file_name = SOURCE.name
        generated_from = str(SOURCE)
    else:
        existing_payload = load_existing_consumption_payload()
        if existing_payload is None:
            raise FileNotFoundError(f"Consumption workbook not found and no generated payload exists: {SOURCE}")
        months = [{"key": str(index), "label": label} for index, label in enumerate(existing_payload["months"])]
        raw_rows = existing_payload["source"].get("rawRows", len(existing_payload["commodities"]))
        blank_product_rows = existing_payload["source"].get("blankProductRows", 0)
        source_rows = [
            {
                "sourceRow": item.get("sourceRow", index + 2),
                "product": item["product"],
                "packSize": item["packSize"],
                "values": item["values"],
            }
            for index, item in enumerate(existing_payload["commodities"])
        ]
        file_name = existing_payload["source"].get("fileName", SOURCE.name)
        generated_from = existing_payload["source"].get("generatedFrom", str(SOURCE))

    commodities = []
    for source_item in source_rows:
        product = source_item["product"]
        pack_size = source_item["packSize"]
        values = source_item["values"]
        adjusted_by_month = adjusted_map.get(commodity_key(product, pack_size), {})
        adjusted_values = []
        difference_values = []
        for month, value in zip(months, values):
            adjusted_value = adjusted_by_month.get(month["label"])
            adjusted_values.append(adjusted_value)
            difference_values.append(adjusted_value - value if adjusted_value is not None else None)

        monthly = [
            {
                "month": months[index]["label"],
                "value": value,
                "adjusted": adjusted_values[index],
                "difference": difference_values[index],
            }
            for index, value in enumerate(values)
        ]
        total = int(sum(values))
        highest_index = max(range(len(values)), key=lambda index: values[index]) if values else 0
        lowest_index = min(range(len(values)), key=lambda index: values[index]) if values else 0

        commodities.append(
            {
                "id": len(commodities) + 1,
                "sourceRow": source_item["sourceRow"],
                "product": product,
                "packSize": pack_size,
                "values": values,
                "adjustedValues": adjusted_values,
                "differenceValues": difference_values,
                "hasAdjusted2025": bool(adjusted_by_month),
                "monthly": monthly,
                "total": total,
                "adjusted2025Total": int(sum(value for value in adjusted_values if value is not None)),
                "difference2025Total": int(sum(value for value in difference_values if value is not None)),
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
            "fileName": file_name,
            "sheet": SHEET_NAME,
            "rawRows": raw_rows,
            "commodityRows": len(commodities),
            "blankProductRows": blank_product_rows,
            "adjustedFileName": ADJUSTED_SOURCE.name,
            "adjustedPairs2025": adjusted_pairs,
            "adjustedMatchedCommodityRows": int(sum(1 for item in commodities if item["hasAdjusted2025"])),
            "generatedFrom": generated_from,
            "adjustedGeneratedFrom": str(ADJUSTED_SOURCE),
            "period": f"{months[0]['label']} to {months[-1]['label']}" if months else "",
            "adjustedPeriod": "Jan 2025 to Dec 2025",
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
