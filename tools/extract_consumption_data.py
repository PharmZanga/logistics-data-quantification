import json
from pathlib import Path

import pandas as pd


SOURCE = Path(r"C:\Users\Zanga Musakuzi\Desktop\adjusted data EM 2025 consumption data.xlsx")
OUTPUT = Path(__file__).resolve().parents[1] / "data" / "dashboard-data.js"

MONTH_COLUMNS = [
    ("JAN", "Jan"),
    ("FEB", "Feb"),
    ("MAR", "Mar"),
    ("APR", "Apr"),
    ("MAY", "May"),
    ("JUN", "Jun"),
    ("JUL", "Jul"),
    ("AUG", "Aug"),
    ("SEP", "Sep"),
    ("OCT", "Oct"),
    ("NOVE", "Nov"),
    ("DEC", "Dec"),
]


def clean_text(value):
    if pd.isna(value):
        return ""
    return " ".join(str(value).strip().split())


def month_value(row, column):
    value = pd.to_numeric(row.get(column), errors="coerce")
    if pd.isna(value):
        return 0
    return int(round(float(value)))


def build_monthly(reported_row, adjusted_row):
    monthly = []
    for raw_month, label in MONTH_COLUMNS:
        reported = month_value(reported_row, raw_month)
        adjusted = month_value(adjusted_row, raw_month) if adjusted_row is not None else 0
        monthly.append(
            {
                "month": label,
                "reported": reported,
                "adjusted": adjusted,
                "difference": adjusted - reported,
            }
        )
    return monthly


def main():
    df = pd.read_excel(SOURCE, sheet_name="Sheet1")
    raw_rows = len(df)

    commodities = []
    adjusted_pair_count = 0
    skipped_blank_rows = 0

    index = 0
    while index < len(df):
        row = df.iloc[index]
        product = clean_text(row.get("Products Description"))

        if not product:
            skipped_blank_rows += 1
            index += 1
            continue

        pack_size = clean_text(row.get("Pack Size")) or "Not specified"
        adjusted_row = None
        if index + 1 < len(df):
            next_row = df.iloc[index + 1]
            next_product = clean_text(next_row.get("Products Description"))
            if not next_product:
                adjusted_row = next_row
                adjusted_pair_count += 1

        monthly = build_monthly(row, adjusted_row)
        reported_values = [entry["reported"] for entry in monthly]
        adjusted_values = [entry["adjusted"] for entry in monthly]
        difference_values = [entry["difference"] for entry in monthly]
        total_reported = int(sum(reported_values))
        total_adjusted = int(sum(adjusted_values))
        highest_entry = max(monthly, key=lambda entry: entry["adjusted"])
        lowest_entry = min(monthly, key=lambda entry: entry["adjusted"])

        commodities.append(
            {
                "id": len(commodities) + 1,
                "sourceRow": index + 2,
                "product": product,
                "packSize": pack_size,
                "hasAdjustedRow": adjusted_row is not None,
                "monthly": monthly,
                "totalReported": total_reported,
                "totalAdjusted": total_adjusted,
                "totalDifference": int(sum(difference_values)),
                "averageAdjusted": round(total_adjusted / 12, 1),
                "highestMonth": highest_entry["month"],
                "highestValue": highest_entry["adjusted"],
                "lowestMonth": lowest_entry["month"],
                "lowestValue": lowest_entry["adjusted"],
            }
        )

        index += 2 if adjusted_row is not None else 1

    payload = {
        "source": {
            "fileName": SOURCE.name,
            "sheet": "Sheet1",
            "rawRows": raw_rows,
            "reportedCommodityRows": len(commodities),
            "adjustedPairs": adjusted_pair_count,
            "unpairedReportedRows": len(commodities) - adjusted_pair_count,
            "skippedBlankRows": skipped_blank_rows,
            "generatedFrom": str(SOURCE),
            "period": "Jan-Dec 2025",
        },
        "months": [label for _, label in MONTH_COLUMNS],
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
    print(f"Reported commodity rows: {len(commodities):,}")
    print(f"Reported rows with adjusted pair: {adjusted_pair_count:,}")


if __name__ == "__main__":
    main()
