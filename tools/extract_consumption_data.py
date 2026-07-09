import json
from datetime import datetime
from pathlib import Path

import pandas as pd


SOURCE = Path(r"C:\Users\Zanga Musakuzi\Downloads\EM CONSUMPTION DATA2024 TO 2026.xlsx")
ADJUSTED_SOURCE = Path(r"C:\Users\Zanga Musakuzi\Desktop\adjusted data EM 2025 consumption data.xlsx")
FORECAST_SOURCE = Path(r"C:\Users\Zanga Musakuzi\Desktop\quantification 2026\FORECAST CONSOLIDATION FP 2023-2026.xlsx")
OUTPUT = Path(__file__).resolve().parents[1] / "data" / "dashboard-data.js"
CODE_CONSUMPTION_SOURCES = {
    "2024": Path(__file__).resolve().parents[1] / "data" / "rh-2024-consumption.tsv",
    "2025": Path(__file__).resolve().parents[1] / "data" / "rh-2025-consumption.tsv",
    "2026": Path(__file__).resolve().parents[1] / "data" / "rh-2026-consumption.tsv",
}
SHEET_NAME = "CONSUMPTION DATA"
ADJUSTED_SHEET_NAME = "Sheet1"
FORECAST_SHEET_NAME = "Sheet1"
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


def product_key(product):
    return clean_text(product).lower()


def apply_code_consumption(item, code_consumption):
    if not code_consumption:
        return item

    item["annualConsumptionByYear"] = {
        **item.get("annualConsumptionByYear", {}),
        **code_consumption.get("annualConsumptionByYear", {}),
    }
    item["annualReportedConsumptionByYear"] = {
        **item.get("annualReportedConsumptionByYear", {}),
        **code_consumption.get("annualReportedConsumptionByYear", {}),
    }
    item["annualAdjustedConsumptionByYear"] = {
        **item.get("annualAdjustedConsumptionByYear", {}),
        **code_consumption.get("annualAdjustedConsumptionByYear", {}),
    }
    item["codeConsumptionRowsByYear"] = {
        **item.get("codeConsumptionRowsByYear", {}),
        **code_consumption.get("sourceRowsByYear", {}),
    }
    item["codeConsumption2024Rows"] = item["codeConsumptionRowsByYear"].get("2024", 0)
    if not item.get("sku"):
        item["sku"] = code_consumption["code"]
    return item


def load_adjusted_2025():
    if not ADJUSTED_SOURCE.exists():
        return {}, 0

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


def load_forecast_commodities():
    if not FORECAST_SOURCE.exists():
        return [], 0

    forecast_df = pd.read_excel(FORECAST_SOURCE, sheet_name=FORECAST_SHEET_NAME, header=1)
    forecast_df.columns = [clean_text(column) for column in forecast_df.columns]
    forecast_items = {}
    usable_rows = 0

    for row_index, row in forecast_df.iterrows():
        fallback_name = clean_text(row.get("PRODUCTS NAME BY FQ"))
        catalogue_name = clean_text(row.get("PRODUCTS NAME BY ZAMMSA CATALOGUE"))
        product = catalogue_name or fallback_name
        if not product:
            continue

        year = pd.to_numeric(row.get("FORECASTED FOR YEAR"), errors="coerce")
        quantity = pd.to_numeric(row.get("FINAL AGREED FORECAST QTY"), errors="coerce")
        if pd.isna(year):
            continue

        usable_rows += 1
        pack_size = clean_text(row.get("FORCAST IN CATALOGUE PACK SIZE")) or clean_text(row.get("UNIT")) or "Not specified"
        key = commodity_key(product, pack_size)
        if key not in forecast_items:
            forecast_items[key] = {
                "sourceRow": int(row_index) + 3,
                "product": product,
                "packSize": pack_size,
                "forecastOnly": True,
                "forecastByYear": {},
                "forecastSourceName": fallback_name,
                "sku": clean_text(row.get("SKU")),
            }

        if not pd.isna(quantity):
            forecast_items[key]["forecastByYear"][str(int(year))] = int(round(float(quantity)))

    return list(forecast_items.values()), usable_rows


def load_code_consumption_by_year():
    code_map = {}
    stats = {year: {"rows": 0, "fileName": source.name if source.exists() else ""} for year, source in CODE_CONSUMPTION_SOURCES.items()}

    for year, source in CODE_CONSUMPTION_SOURCES.items():
        if not source.exists():
            continue

        for raw_line in source.read_text(encoding="utf-8").splitlines():
            if not raw_line.strip():
                continue
            parts = raw_line.split("\t")
            if len(parts) < 4:
                continue

            code = clean_text(parts[0]).upper()
            product = clean_text(parts[1]).replace("FALSE", "no")
            numeric_parts = parts[-3:] if len(parts) >= 5 else [parts[-2], parts[-1], parts[-2]]
            values = [pd.to_numeric(value, errors="coerce") for value in numeric_parts]
            if not code.startswith("RH") or any(pd.isna(value) for value in values):
                continue

            stats[year]["rows"] += 1
            if code not in code_map:
                code_map[code] = {
                    "code": code,
                    "product": product,
                    "sourceRowsByYear": {},
                    "annualReportedConsumptionByYear": {},
                    "annualAdjustedConsumptionByYear": {},
                    "annualConsumptionByYear": {},
                }

            item = code_map[code]
            if len(product) > len(item["product"]):
                item["product"] = product
            item["sourceRowsByYear"][year] = item["sourceRowsByYear"].get(year, 0) + 1
            item["annualReportedConsumptionByYear"][year] = item["annualReportedConsumptionByYear"].get(year, 0) + int(round(float(values[0])))
            item["annualAdjustedConsumptionByYear"][year] = item["annualAdjustedConsumptionByYear"].get(year, 0) + int(round(float(values[1])))
            item["annualConsumptionByYear"][year] = item["annualConsumptionByYear"].get(year, 0) + int(round(float(values[2])))

    return code_map, stats


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
    forecast_items, forecast_rows = load_forecast_commodities()
    code_consumption_map, code_consumption_stats = load_code_consumption_by_year()
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
                "adjustedValues": item.get("adjustedValues", []),
                "differenceValues": item.get("differenceValues", []),
                "hasAdjusted2025": item.get("hasAdjusted2025", False),
                "forecastOnly": item.get("forecastOnly", False),
                "forecastByYear": item.get("forecastByYear", {}),
                "forecastSourceName": item.get("forecastSourceName", ""),
                "sku": item.get("sku", ""),
                "annualConsumptionByYear": item.get("annualConsumptionByYear", {}),
                "annualReportedConsumptionByYear": item.get("annualReportedConsumptionByYear", {}),
                "annualAdjustedConsumptionByYear": item.get("annualAdjustedConsumptionByYear", {}),
                "codeConsumptionRowsByYear": item.get("codeConsumptionRowsByYear", {}),
                "codeConsumption2024Rows": item.get("codeConsumption2024Rows", 0),
            }
            for index, item in enumerate(existing_payload["commodities"])
        ]
        file_name = existing_payload["source"].get("fileName", SOURCE.name)
        generated_from = existing_payload["source"].get("generatedFrom", str(SOURCE))
        if not adjusted_map:
            adjusted_pairs = existing_payload["source"].get("adjustedPairs2025", 0)

    used_codes = set()
    for source_item in source_rows:
        code = clean_text(source_item.get("sku")).upper()
        if code in code_consumption_map:
            apply_code_consumption(source_item, code_consumption_map[code])
            used_codes.add(code)

    for forecast_item in forecast_items:
        code = clean_text(forecast_item.get("sku")).upper()
        if code in code_consumption_map:
            apply_code_consumption(forecast_item, code_consumption_map[code])
            used_codes.add(code)

    existing_product_keys = {product_key(item["product"]) for item in source_rows}
    forecast_added = 0
    for forecast_item in forecast_items:
        if product_key(forecast_item["product"]) in existing_product_keys:
            continue
        forecast_item["values"] = [None for _ in months]
        source_rows.append(forecast_item)
        existing_product_keys.add(product_key(forecast_item["product"]))
        forecast_added += 1

    code_consumption_added = 0
    for code, code_item in sorted(code_consumption_map.items()):
        if code in used_codes:
            continue
        product = code_item["product"] or code
        source_rows.append(
            apply_code_consumption(
                {
                    "sourceRow": 0,
                    "product": product,
                    "packSize": code,
                    "values": [None for _ in months],
                    "forecastOnly": True,
                    "forecastByYear": {},
                    "forecastSourceName": "",
                    "sku": code,
                },
                code_item,
            )
        )
        used_codes.add(code)
        code_consumption_added += 1

    commodities = []
    for source_item in source_rows:
        product = source_item["product"]
        pack_size = source_item["packSize"]
        values = source_item["values"]
        adjusted_by_month = adjusted_map.get(commodity_key(product, pack_size), {})
        stored_adjusted_values = source_item.get("adjustedValues", [])
        stored_difference_values = source_item.get("differenceValues", [])
        if adjusted_by_month:
            adjusted_values = []
            difference_values = []
            for month, value in zip(months, values):
                adjusted_value = adjusted_by_month.get(month["label"])
                adjusted_values.append(adjusted_value)
                difference_values.append(adjusted_value - value if adjusted_value is not None and value is not None else None)
        elif len(stored_adjusted_values) == len(values):
            adjusted_values = stored_adjusted_values
            difference_values = (
                stored_difference_values
                if len(stored_difference_values) == len(values)
                else [
                    adjusted_value - value if adjusted_value is not None and value is not None else None
                    for adjusted_value, value in zip(adjusted_values, values)
                ]
            )
        else:
            adjusted_values = [None for _ in values]
            difference_values = [None for _ in values]

        monthly = [
            {
                "month": months[index]["label"],
                "value": value,
                "adjusted": adjusted_values[index],
                "difference": difference_values[index],
            }
            for index, value in enumerate(values)
        ]
        numeric_values = [0 if value is None else value for value in values]
        total = int(sum(numeric_values))
        highest_index = max(range(len(numeric_values)), key=lambda index: numeric_values[index]) if numeric_values else 0
        lowest_index = min(range(len(numeric_values)), key=lambda index: numeric_values[index]) if numeric_values else 0

        commodities.append(
            {
                "id": len(commodities) + 1,
                "sourceRow": source_item["sourceRow"],
                "product": product,
                "packSize": pack_size,
                "values": values,
                "adjustedValues": adjusted_values,
                "differenceValues": difference_values,
                "hasAdjusted2025": bool(adjusted_by_month) or bool(source_item.get("hasAdjusted2025", False)),
                "forecastOnly": bool(source_item.get("forecastOnly", False)),
                "forecastByYear": source_item.get("forecastByYear", {}),
                "forecastSourceName": source_item.get("forecastSourceName", ""),
                "sku": source_item.get("sku", ""),
                "annualConsumptionByYear": source_item.get("annualConsumptionByYear", {}),
                "annualReportedConsumptionByYear": source_item.get("annualReportedConsumptionByYear", {}),
                "annualAdjustedConsumptionByYear": source_item.get("annualAdjustedConsumptionByYear", {}),
                "codeConsumptionRowsByYear": source_item.get("codeConsumptionRowsByYear", {}),
                "codeConsumption2024Rows": source_item.get("codeConsumption2024Rows", 0),
                "monthly": monthly,
                "total": total,
                "adjusted2025Total": int(sum(value for value in adjusted_values if value is not None)),
                "difference2025Total": int(sum(value for value in difference_values if value is not None)),
                "averageMonthly": round(total / len(numeric_values), 1) if numeric_values else 0,
                "activeMonths": int(sum(1 for value in numeric_values if value > 0)),
                "highestMonth": months[highest_index]["label"] if values else "",
                "highestValue": numeric_values[highest_index] if numeric_values else 0,
                "lowestMonth": months[lowest_index]["label"] if values else "",
                "lowestValue": numeric_values[lowest_index] if numeric_values else 0,
            }
        )

    totals_by_month = []
    for index, month in enumerate(months):
        totals_by_month.append(
            {
                "month": month["label"],
                "value": int(sum((item["values"][index] or 0) for item in commodities)),
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
            "forecastFileName": FORECAST_SOURCE.name if FORECAST_SOURCE.exists() else "",
            "forecastRows": forecast_rows,
            "forecastOnlyCommodityRows": forecast_added,
            "codeConsumptionFileNamesByYear": {year: stat["fileName"] for year, stat in code_consumption_stats.items() if stat["fileName"]},
            "codeConsumptionRowsByYear": {year: stat["rows"] for year, stat in code_consumption_stats.items() if stat["rows"]},
            "codeConsumption2024FileName": code_consumption_stats.get("2024", {}).get("fileName", ""),
            "codeConsumption2024Rows": code_consumption_stats.get("2024", {}).get("rows", 0),
            "codeConsumptionCodes": len(code_consumption_map),
            "codeConsumption2024Codes": len(code_consumption_map),
            "codeConsumption2024OnlyCommodityRows": code_consumption_added,
            "generatedFrom": generated_from,
            "adjustedGeneratedFrom": str(ADJUSTED_SOURCE),
            "forecastGeneratedFrom": str(FORECAST_SOURCE) if FORECAST_SOURCE.exists() else "",
            "period": f"{months[0]['label']} to {months[-1]['label']}" if months else "",
            "adjustedPeriod": "Jan 2025 to Dec 2025",
            "forecastPeriod": "2023 to 2026" if forecast_rows else "",
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
    print(f"Forecast-only rows added: {forecast_added:,}")
    print(f"Annual RH consumption codes added: {code_consumption_added:,}")
    print(f"Period: {payload['source']['period']}")


if __name__ == "__main__":
    main()
