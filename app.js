const data = window.NSCCU_DASHBOARD_DATA;
const state = {
  search: "",
  selectedId: data.commodities[0]?.id || null,
};

const els = {
  sourceFile: document.getElementById("sourceFile"),
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
  tableNote: document.getElementById("tableNote"),
  downloadButton: document.getElementById("downloadButton"),
  qualityNote: document.getElementById("qualityNote"),
};

const fmt = new Intl.NumberFormat("en-US");

function formatNumber(value) {
  return fmt.format(Math.round(Number(value) || 0));
}

function optionLabel(item) {
  return `${item.product} | ${item.packSize} | Row ${item.sourceRow}`;
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

function drawChartFrame(ctx, width, height, padding, minValue, maxValue) {
  const chartHeight = height - padding.top - padding.bottom;
  ctx.strokeStyle = "#dce5ec";
  ctx.fillStyle = "#5d6b78";
  ctx.font = "12px Segoe UI, Arial";
  ctx.lineWidth = 1;

  for (let i = 0; i <= 4; i += 1) {
    const y = padding.top + chartHeight - (chartHeight * i) / 4;
    const value = minValue + ((maxValue - minValue) * i) / 4;
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();
    ctx.fillText(formatNumber(value), 10, y + 4);
  }
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

function drawComparisonChart(item) {
  const { ctx, width, height } = setupCanvas(els.comparisonChart);
  const padding = { top: 24, right: 32, bottom: 48, left: 92 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const values = item.monthly.flatMap((entry) => [entry.reported, entry.adjusted]);
  const maxValue = Math.max(...values, 1);

  drawChartFrame(ctx, width, height, padding, 0, maxValue);

  function pointFor(entry, index, field) {
    return {
      x: padding.left + (chartWidth * index) / Math.max(item.monthly.length - 1, 1),
      y: padding.top + chartHeight - (entry[field] / maxValue) * chartHeight,
    };
  }

  function drawLine(field, color) {
    ctx.beginPath();
    item.monthly.forEach((entry, index) => {
      const point = pointFor(entry, index, field);
      if (index === 0) ctx.moveTo(point.x, point.y);
      else ctx.lineTo(point.x, point.y);
    });
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.stroke();

    item.monthly.forEach((entry, index) => {
      const point = pointFor(entry, index, field);
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(point.x, point.y, 4, 0, Math.PI * 2);
      ctx.fill();
    });
  }

  drawLine("reported", "#1d4ed8");
  drawLine("adjusted", "#0f766e");

  ctx.fillStyle = "#5d6b78";
  ctx.textAlign = "center";
  item.monthly.forEach((entry, index) => {
    const x = padding.left + (chartWidth * index) / Math.max(item.monthly.length - 1, 1);
    ctx.fillText(entry.month, x, height - 20);
  });

  ctx.textAlign = "left";
  ctx.fillStyle = "#1d4ed8";
  ctx.fillRect(width - 190, 18, 12, 12);
  ctx.fillText("Reported", width - 172, 29);
  ctx.fillStyle = "#0f766e";
  ctx.fillRect(width - 105, 18, 12, 12);
  ctx.fillText("Adjusted", width - 87, 29);
}

function drawDifferenceChart(item) {
  const { ctx, width, height } = setupCanvas(els.differenceChart);
  const padding = { top: 24, right: 28, bottom: 48, left: 92 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const values = item.monthly.map((entry) => entry.difference);
  const maxAbs = Math.max(...values.map(Math.abs), 1);
  const minValue = -maxAbs;
  const maxValue = maxAbs;
  const zeroY = padding.top + chartHeight - ((0 - minValue) / (maxValue - minValue)) * chartHeight;

  drawChartFrame(ctx, width, height, padding, minValue, maxValue);
  ctx.strokeStyle = "#17212b";
  ctx.beginPath();
  ctx.moveTo(padding.left, zeroY);
  ctx.lineTo(width - padding.right, zeroY);
  ctx.stroke();

  const gap = 12;
  const barWidth = Math.max(14, (chartWidth - gap * (item.monthly.length - 1)) / item.monthly.length);
  item.monthly.forEach((entry, index) => {
    const x = padding.left + index * (barWidth + gap);
    const y = padding.top + chartHeight - ((entry.difference - minValue) / (maxValue - minValue)) * chartHeight;
    const barTop = Math.min(y, zeroY);
    const barHeight = Math.abs(zeroY - y);
    ctx.fillStyle = entry.difference >= 0 ? "#0f766e" : "#b91c1c";
    ctx.fillRect(x, barTop, barWidth, Math.max(1, barHeight));
    ctx.save();
    ctx.translate(x + barWidth / 2, height - 20);
    ctx.rotate(-Math.PI / 5);
    ctx.fillStyle = "#5d6b78";
    ctx.textAlign = "right";
    ctx.fillText(entry.month, 0, 0);
    ctx.restore();
  });
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
  els.kpiReported.textContent = formatNumber(item.totalReported);
  els.kpiAdjusted.textContent = formatNumber(item.totalAdjusted);
  els.kpiAverage.textContent = formatNumber(item.averageAdjusted);
  els.kpiHighest.textContent = `${item.highestMonth} (${formatNumber(item.highestValue)})`;
  els.kpiLowest.textContent = `${item.lowestMonth} (${formatNumber(item.lowestValue)})`;
}

function renderProduct(item) {
  els.productName.textContent = item.product;
  els.packSize.textContent = item.packSize;
  els.pairStatus.textContent = item.hasAdjustedRow ? "Adjusted consumption row found" : "No adjusted row found; adjusted values are zero";
}

function renderTable(item) {
  els.monthlyTable.innerHTML = item.monthly
    .map(
      (entry) => `
        <tr>
          <td>${entry.month} 2025</td>
          <td class="num">${formatNumber(entry.reported)}</td>
          <td class="num">${formatNumber(entry.adjusted)}</td>
          <td class="num ${entry.difference < 0 ? "negative" : entry.difference > 0 ? "positive" : ""}">${formatNumber(entry.difference)}</td>
        </tr>
      `,
    )
    .join("");
  els.tableNote.textContent = `Difference = adjusted minus reported for ${item.product}`;
}

function render() {
  renderOptions();
  const item = selectedCommodity();
  if (!item) return;
  renderProduct(item);
  renderKpis(item);
  renderTable(item);
  drawComparisonChart(item);
  drawDifferenceChart(item);
}

function downloadCsv() {
  const item = selectedCommodity();
  const headers = ["Product", "Pack Size", "Month", "Reported Consumption", "Adjusted Consumption", "Difference"];
  const rows = item.monthly.map((entry) => [item.product, item.packSize, `${entry.month} 2025`, entry.reported, entry.adjusted, entry.difference]);
  const csv = [headers, ...rows]
    .map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(","))
    .join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "commodity-reported-adjusted-consumption.csv";
  link.click();
  URL.revokeObjectURL(link.href);
}

function init() {
  if (els.sourceFile) {
    els.sourceFile.textContent = data.source.fileName;
  }
  els.qualityNote.textContent = `${formatNumber(data.source.rawRows)} Excel rows were read from ${data.source.sheet}. ${formatNumber(
    data.source.reportedCommodityRows,
  )} named product rows were loaded as reported consumption. ${formatNumber(
    data.source.adjustedPairs,
  )} products had a blank row immediately after them and that row was used as adjusted consumption. Missing monthly cells are treated as zero.`;

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
