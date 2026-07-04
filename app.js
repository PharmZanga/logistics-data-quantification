const data = window.NSCCU_DASHBOARD_DATA;
const state = {
  search: "",
  selectedId: data.commodities[0]?.id || null,
};

const els = {
  searchInput: document.getElementById("searchInput"),
  commoditySelect: document.getElementById("commoditySelect"),
  resetButton: document.getElementById("resetButton"),
  productName: document.getElementById("productName"),
  packSize: document.getElementById("packSize"),
  pairStatus: document.getElementById("pairStatus"),
  kpiReported: document.getElementById("kpiReported"),
  kpiAdjusted: document.getElementById("kpiAdjusted"),
  kpiAverage: document.getElementById("kpiAverage"),
  kpiHighest: document.getElementById("kpiHighest"),
  kpiLowest: document.getElementById("kpiLowest"),
  comparisonChart: document.getElementById("comparisonChart"),
  differenceChart: document.getElementById("differenceChart"),
  monthlyTable: document.getElementById("monthlyTable"),
  tableHead: document.getElementById("tableHead"),
  tableNote: document.getElementById("tableNote"),
  downloadButton: document.getElementById("downloadButton"),
  qualityNote: document.getElementById("qualityNote"),
};

const fmt = new Intl.NumberFormat("en-US");

function formatNumber(value) {
  if (value === null || value === undefined) return "-";
  return fmt.format(Math.round(Number(value) || 0));
}

function optionLabel(item) {
  return `${item.product} | ${item.packSize}`;
}

function filteredCommodities() {
  const term = state.search.trim().toLowerCase();
  if (!term) return data.commodities;
  return data.commodities.filter((item) => `${item.product} ${item.packSize}`.toLowerCase().includes(term));
}

function selectedCommodity() {
  return data.commodities.find((item) => item.id === Number(state.selectedId)) || data.commodities[0];
}

function setSelectedToFirstVisible() {
  const visible = filteredCommodities();
  state.selectedId = visible[0]?.id || data.commodities[0]?.id || null;
}

function setupCanvas(canvas) {
  const ctx = canvas.getContext("2d");
  const width = canvas.clientWidth;
  const height = Number(canvas.getAttribute("height"));
  const dpr = window.devicePixelRatio || 1;
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, width, height);
  return { ctx, width, height };
}

function drawFrame(ctx, width, height, padding, maxValue) {
  const chartHeight = height - padding.top - padding.bottom;
  ctx.strokeStyle = "#dce5ec";
  ctx.fillStyle = "#5d6b78";
  ctx.font = "12px Segoe UI, Arial";
  for (let i = 0; i <= 4; i += 1) {
    const y = padding.top + chartHeight - (chartHeight * i) / 4;
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();
    ctx.fillText(formatNumber((maxValue * i) / 4), 10, y + 4);
  }
}

function drawConsumptionTrend(item) {
  const { ctx, width, height } = setupCanvas(els.comparisonChart);
  const padding = { top: 24, right: 32, bottom: 64, left: 92 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const consumptionValues = item.values.filter((value) => value !== null && value !== undefined);
  const adjustedOnly = item.adjustedValues.filter((value) => value !== null && value !== undefined);
  const maxValue = Math.max(...consumptionValues, ...adjustedOnly, 1);

  drawFrame(ctx, width, height, padding, maxValue);

  function pointsFor(field) {
    return item.monthly
      .map((entry, index) => {
        const value = entry[field];
        if (value === null || value === undefined) return null;
        return {
          x: padding.left + (chartWidth * index) / Math.max(item.monthly.length - 1, 1),
          y: padding.top + chartHeight - (value / maxValue) * chartHeight,
          label: entry.month,
        };
      })
      .filter(Boolean);
  }

  function drawLine(field, color) {
    const points = pointsFor(field);
    ctx.beginPath();
    points.forEach((point, index) => {
      if (index === 0) ctx.moveTo(point.x, point.y);
      else ctx.lineTo(point.x, point.y);
    });
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.stroke();

    points.forEach((point) => {
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(point.x, point.y, 3.5, 0, Math.PI * 2);
      ctx.fill();
    });
  }

  drawLine("value", "#0f766e");
  drawLine("adjusted", "#1d4ed8");

  item.monthly.forEach((entry, index) => {
    if (index % 2 === 0 || item.monthly.length <= 16) {
      const x = padding.left + (chartWidth * index) / Math.max(item.monthly.length - 1, 1);
      ctx.save();
      ctx.translate(x, height - 20);
      ctx.rotate(-Math.PI / 5);
      ctx.fillStyle = "#5d6b78";
      ctx.textAlign = "right";
      ctx.fillText(entry.month, 0, 0);
      ctx.restore();
    }
  });

  ctx.textAlign = "left";
  ctx.fillStyle = "#0f766e";
  ctx.fillRect(width - 230, 18, 12, 12);
  ctx.fillText("Consumption", width - 212, 29);
  ctx.fillStyle = "#1d4ed8";
  ctx.fillRect(width - 125, 18, 12, 12);
  ctx.fillText("Adjusted", width - 107, 29);
}

function drawAnnualChart(item) {
  const { ctx, width, height } = setupCanvas(els.differenceChart);
  const padding = { top: 24, right: 30, bottom: 44, left: 92 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  let rows = [];
  if (item.forecastOnly && item.forecastByYear) {
    rows = Object.entries(item.forecastByYear).map(([year, value]) => ({ year, value }));
  } else {
    const annual = {};
    item.monthly.forEach((entry) => {
      const year = entry.month.split(" ")[1] || "";
      annual[year] = (annual[year] || 0) + (entry.value || 0);
    });
    rows = Object.entries(annual).map(([year, value]) => ({ year, value }));
  }
  const maxValue = Math.max(...rows.map((row) => row.value), 1);

  drawFrame(ctx, width, height, padding, maxValue);

  const gap = 30;
  const barWidth = Math.max(42, (chartWidth - gap * (rows.length - 1)) / Math.max(rows.length, 1));
  rows.forEach((row, index) => {
    const x = padding.left + index * (barWidth + gap);
    const barHeight = (row.value / maxValue) * chartHeight;
    const y = padding.top + chartHeight - barHeight;
    ctx.fillStyle = index === rows.length - 1 ? "#19d4e7" : "#0f766e";
    ctx.fillRect(x, y, barWidth, barHeight);
    ctx.fillStyle = "#17212b";
    ctx.textAlign = "center";
    ctx.fillText(row.year, x + barWidth / 2, height - 18);
    ctx.fillStyle = "#5d6b78";
    ctx.fillText(formatNumber(row.value), x + barWidth / 2, y - 8);
  });
  ctx.textAlign = "left";
}

function renderOptions() {
  const visible = filteredCommodities();
  const selectedStillVisible = visible.some((item) => item.id === Number(state.selectedId));
  if (!selectedStillVisible) setSelectedToFirstVisible();

  els.commoditySelect.innerHTML = visible
    .map((item) => `<option value="${item.id}" ${item.id === Number(state.selectedId) ? "selected" : ""}>${optionLabel(item)}</option>`)
    .join("");
}

function renderKpis(item) {
  els.kpiReported.textContent = item.forecastOnly ? "-" : formatNumber(item.total);
  els.kpiAdjusted.textContent = item.hasAdjusted2025 ? formatNumber(item.adjusted2025Total) : "-";
  els.kpiAverage.textContent = item.forecastOnly ? "-" : formatNumber(item.averageMonthly);
  els.kpiHighest.textContent = item.forecastOnly ? "-" : `${item.highestMonth} (${formatNumber(item.highestValue)})`;
  els.kpiLowest.textContent = item.forecastOnly ? "-" : `${item.lowestMonth} (${formatNumber(item.lowestValue)})`;
}

function renderProduct(item) {
  els.productName.textContent = item.product;
  els.packSize.textContent = item.packSize;
  if (item.forecastOnly) {
    const sku = item.sku ? ` SKU ${item.sku}.` : "";
    els.pairStatus.textContent = `Forecast-only commodity added from the 2023-2026 consolidation workbook.${sku}`;
    return;
  }
  els.pairStatus.textContent = item.hasAdjusted2025 ? "2025 adjusted data matched" : "No 2025 adjusted row matched";
}

function valueClass(value) {
  if (value === null || value === undefined || value === 0) return "";
  return value > 0 ? "positive" : "negative";
}

function renderWideTable(item) {
  els.tableHead.innerHTML = `
    <tr>
      <th>Product Description</th>
      <th>Pack Size</th>
      <th>Data Type</th>
      ${data.months.map((month) => `<th class="num">${month}</th>`).join("")}
    </tr>
  `;

  els.monthlyTable.innerHTML = `
    <tr class="selected-row" data-id="${item.id}">
      <td>${item.product}</td>
      <td>${item.packSize}</td>
      <td>Consumption</td>
      ${item.values.map((value) => `<td class="num">${formatNumber(value)}</td>`).join("")}
    </tr>
    <tr>
      <td>${item.product}</td>
      <td>${item.packSize}</td>
      <td>Adjusted Consumption</td>
      ${item.adjustedValues.map((value) => `<td class="num">${formatNumber(value)}</td>`).join("")}
    </tr>
    <tr>
      <td>${item.product}</td>
      <td>${item.packSize}</td>
      <td>Difference</td>
      ${item.differenceValues.map((value) => `<td class="num ${valueClass(value)}">${formatNumber(value)}</td>`).join("")}
    </tr>
  `;

  els.tableNote.textContent = item.forecastOnly
    ? `Showing selected forecast-only commodity: ${item.product}. Monthly consumption will remain blank until a consumption workbook is uploaded.`
    : `Showing selected commodity only: ${item.product}`;
}

function render() {
  renderOptions();
  const item = selectedCommodity();
  if (!item) return;
  renderProduct(item);
  renderKpis(item);
  renderWideTable(item);
  drawConsumptionTrend(item);
  drawAnnualChart(item);
}

function downloadCsv() {
  const item = selectedCommodity();
  const headers = ["Product Description", "Pack Size", "Data Type", ...data.months];
  const body = [
    [item.product, item.packSize, "Consumption", ...item.values],
    [item.product, item.packSize, "Adjusted Consumption", ...item.adjustedValues.map((value) => value ?? "")],
    [item.product, item.packSize, "Difference", ...item.differenceValues.map((value) => value ?? "")],
  ];
  const csv = [headers, ...body]
    .map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(","))
    .join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "em-consumption-adjusted-difference.csv";
  link.click();
  URL.revokeObjectURL(link.href);
}

function init() {
  const forecastNote = data.source.forecastOnlyCommodityRows
    ? ` ${formatNumber(data.source.forecastOnlyCommodityRows)} forecast-only commodities were added from ${data.source.forecastFileName}.`
    : "";
  els.qualityNote.textContent = `${formatNumber(data.source.rawRows)} Excel rows were read from ${data.source.sheet}. ${formatNumber(
    data.source.commodityRows,
  )} commodity rows are shown from ${data.source.period}. 2025 adjusted consumption is matched from ${data.source.adjustedFileName}; ${formatNumber(
    data.source.adjustedMatchedCommodityRows,
  )} selected consumption rows have a matching adjusted row.${forecastNote} Adjusted cells outside 2025 show as unavailable until those files are uploaded.`;

  els.searchInput.addEventListener("input", (event) => {
    state.search = event.target.value;
    render();
  });
  els.commoditySelect.addEventListener("change", (event) => {
    state.selectedId = Number(event.target.value);
    render();
  });
  els.resetButton.addEventListener("click", () => {
    state.search = "";
    els.searchInput.value = "";
    state.selectedId = data.commodities[0]?.id || null;
    render();
  });
  els.downloadButton.addEventListener("click", downloadCsv);
  window.addEventListener("resize", render);
  render();
}

init();
