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


def main():
    df = pd.read_excel(SOURCE, sheet_name="Sheet1")
    raw_rows = len(df)
    blank_product_rows = int(df["Products Description"].isna().sum())

    df = df[df["Products Description"].notna()].copy()
    df["Products Description"] = df["Products Description"].map(clean_text)
    df["Pack Size"] = df["Pack Size"].map(clean_text)
    for raw_month, _ in MONTH_COLUMNS:
        df[raw_month] = pd.to_numeric(df[raw_month], errors="coerce").fillna(0)

    grouped = (
        df.groupby(["Products Description", "Pack Size"], dropna=False)[[m[0] for m in MONTH_COLUMNS]]
        .sum()
        .reset_index()
    )

    records = []
    totals_by_month = {label: 0 for _, label in MONTH_COLUMNS}
    for index, row in grouped.iterrows():
        monthly = []
        values = []
        for raw_month, label in MONTH_COLUMNS:
            value = int(round(float(row[raw_month])))
            monthly.append({"month": label, "value": value})
            values.append(value)
            totals_by_month[label] += value

        total = int(sum(values))
        active_months = sum(1 for value in values if value > 0)
        average = total / 12 if values else 0
        peak = max(values) if values else 0
        low_nonzero = min([value for value in values if value > 0], default=0)
        volatility = 0
        if average > 0:
            volatility = float(pd.Series(values).std(ddof=0) / average)

        records.append(
            {
                "id": index + 1,
                "product": row["Products Description"],
                "packSize": row["Pack Size"] or "Not specified",
                "monthly": monthly,
                "total": total,
                "averageMonthly": round(average, 1),
                "activeMonths": active_months,
                "peakMonth": MONTH_COLUMNS[values.index(peak)][1] if values else "",
                "peakValue": peak,
                "lowNonZero": low_nonzero,
                "volatility": round(volatility, 3),
            }
        )

    records.sort(key=lambda item: item["total"], reverse=True)
    grand_total = sum(item["total"] for item in records)
    cumulative = 0
    for rank, item in enumerate(records, start=1):
        cumulative += item["total"]
        item["rank"] = rank
        share = item["total"] / grand_total if grand_total else 0
        item["share"] = round(share, 5)
        item["abcClass"] = "A" if cumulative / grand_total <= 0.8 else "B" if cumulative / grand_total <= 0.95 else "C"

    payload = {
        "source": {
            "fileName": SOURCE.name,
            "sheet": "Sheet1",
            "rawRows": raw_rows,
            "namedCommodityRows": int(len(df)),
            "blankProductRows": blank_product_rows,
            "aggregatedCommodities": len(records),
            "generatedFrom": str(SOURCE),
            "period": "2025",
        },
        "months": [label for _, label in MONTH_COLUMNS],
        "totalsByMonth": [{"month": month, "value": value} for month, value in totals_by_month.items()],
        "commodities": records,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "window.NSCCU_DASHBOARD_DATA = "
        + json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT}")
    print(f"Aggregated commodities: {len(records):,}")
    print(f"Grand total: {grand_total:,}")


if __name__ == "__main__":
    main()
