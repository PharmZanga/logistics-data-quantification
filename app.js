const data = window.NSCCU_DASHBOARD_DATA;
const state = {
  search: "",
  pack: "all",
  abc: "all",
  band: "all",
};

const els = {
  sourceFile: document.getElementById("sourceFile"),
  searchInput: document.getElementById("searchInput"),
  packFilter: document.getElementById("packFilter"),
  abcFilter: document.getElementById("abcFilter"),
  bandFilter: document.getElementById("bandFilter"),
  resetButton: document.getElementById("resetButton"),
  kpiTotal: document.getElementById("kpiTotal"),
  kpiCommodities: document.getElementById("kpiCommodities"),
  kpiMonthly: document.getElementById("kpiMonthly"),
  kpiPeak: document.getElementById("kpiPeak"),
  trendNote: document.getElementById("trendNote"),
  monthlyChart: document.getElementById("monthlyChart"),
  topChart: document.getElementById("topChart"),
  abcChart: document.getElementById("abcChart"),
  table: document.getElementById("commodityTable"),
  tableNote: document.getElementById("tableNote"),
  downloadButton: document.getElementById("downloadButton"),
  qualityNote: document.getElementById("qualityNote"),
};

const fmt = new Intl.NumberFormat("en-US");

function formatNumber(value) {
  return fmt.format(Math.round(value || 0));
}

function getBand(item) {
  if (item.total >= 1000000) return "high";
  if (item.activeMonths >= 9) return "steady";
  return "intermittent";
}

function filteredData() {
  const term = state.search.trim().toLowerCase();
  return data.commodities.filter((item) => {
    const matchesSearch = !term || item.product.toLowerCase().includes(term);
    const matchesPack = state.pack === "all" || item.packSize === state.pack;
    const matchesAbc = state.abc === "all" || item.abcClass === state.abc;
    const matchesBand = state.band === "all" || getBand(item) === state.band;
    return matchesSearch && matchesPack && matchesAbc && matchesBand;
  });
}

function monthTotals(items) {
  return data.months.map((month) => ({
    month,
    value: items.reduce((sum, item) => {
      const hit = item.monthly.find((entry) => entry.month === month);
      return sum + (hit ? hit.value : 0);
    }, 0),
  }));
}

function drawBarChart(canvas, rows, options = {}) {
  const ctx = canvas.getContext("2d");
  const width = canvas.clientWidth;
  const height = Number(canvas.getAttribute("height"));
  const dpr = window.devicePixelRatio || 1;
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, width, height);

  const padding = { top: 22, right: 28, bottom: options.bottom || 54, left: options.left || 92 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const maxValue = Math.max(...rows.map((row) => row.value), 1);

  ctx.strokeStyle = "#dce5ec";
  ctx.lineWidth = 1;
  ctx.font = "12px Segoe UI, Arial";
  ctx.fillStyle = "#5d6b78";
  for (let i = 0; i <= 4; i += 1) {
    const y = padding.top + chartHeight - (chartHeight * i) / 4;
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();
    ctx.fillText(formatNumber((maxValue * i) / 4), 10, y + 4);
  }

  const barGap = options.horizontal ? 9 : 14;
  if (options.horizontal) {
    const barHeight = Math.max(12, (chartHeight - barGap * (rows.length - 1)) / rows.length);
    rows.forEach((row, index) => {
      const y = padding.top + index * (barHeight + barGap);
      const barWidth = (row.value / maxValue) * chartWidth;
      ctx.fillStyle = row.color || "#0f766e";
      ctx.fillRect(padding.left, y, barWidth, barHeight);
      ctx.fillStyle = "#17212b";
      ctx.font = "12px Segoe UI, Arial";
      ctx.fillText(row.label.slice(0, 30), 10, y + barHeight - 3);
      ctx.fillStyle = "#5d6b78";
      ctx.fillText(formatNumber(row.value), padding.left + barWidth + 6, y + barHeight - 3);
    });
    return;
  }

  const barWidth = Math.max(12, (chartWidth - barGap * (rows.length - 1)) / rows.length);
  rows.forEach((row, index) => {
    const x = padding.left + index * (barWidth + barGap);
    const barHeight = (row.value / maxValue) * chartHeight;
    const y = padding.top + chartHeight - barHeight;
    ctx.fillStyle = row.color || "#1d4ed8";
    ctx.fillRect(x, y, barWidth, barHeight);
    ctx.save();
    ctx.translate(x + barWidth / 2, height - 18);
    ctx.rotate(-Math.PI / 5);
    ctx.fillStyle = "#5d6b78";
    ctx.textAlign = "right";
    ctx.fillText(row.label, 0, 0);
    ctx.restore();
  });
}

function drawLineChart(canvas, rows) {
  const ctx = canvas.getContext("2d");
  const width = canvas.clientWidth;
  const height = Number(canvas.getAttribute("height"));
  const dpr = window.devicePixelRatio || 1;
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, width, height);

  const padding = { top: 24, right: 30, bottom: 42, left: 86 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const maxValue = Math.max(...rows.map((row) => row.value), 1);

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

  const points = rows.map((row, index) => ({
    x: padding.left + (chartWidth * index) / Math.max(rows.length - 1, 1),
    y: padding.top + chartHeight - (row.value / maxValue) * chartHeight,
    label: row.month,
    value: row.value,
  }));

  ctx.beginPath();
  points.forEach((point, index) => {
    if (index === 0) ctx.moveTo(point.x, point.y);
    else ctx.lineTo(point.x, point.y);
  });
  ctx.strokeStyle = "#0f766e";
  ctx.lineWidth = 3;
  ctx.stroke();

  points.forEach((point) => {
    ctx.fillStyle = "#0f766e";
    ctx.beginPath();
    ctx.arc(point.x, point.y, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#5d6b78";
    ctx.textAlign = "center";
    ctx.fillText(point.label, point.x, height - 18);
  });
  ctx.textAlign = "left";
}

function drawAbcChart(canvas, items) {
  const colors = { A: "#0f766e", B: "#1d4ed8", C: "#b7791f" };
  const totals = ["A", "B", "C"].map((abc) => ({
    label: `Class ${abc}`,
    value: items.filter((item) => item.abcClass === abc).reduce((sum, item) => sum + item.total, 0),
    color: colors[abc],
  }));
  drawBarChart(canvas, totals, { left: 86, bottom: 54 });
}

function updateKpis(items) {
  const total = items.reduce((sum, item) => sum + item.total, 0);
  const monthly = total / 12;
  const monthlyRows = monthTotals(items);
  const peak = monthlyRows.reduce((best, row) => (row.value > best.value ? row : best), monthlyRows[0]);

  els.kpiTotal.textContent = formatNumber(total);
  els.kpiCommodities.textContent = formatNumber(items.length);
  els.kpiMonthly.textContent = formatNumber(monthly);
  els.kpiPeak.textContent = peak ? `${peak.month} (${formatNumber(peak.value)})` : "-";
  els.trendNote.textContent = `${formatNumber(total)} units across selected commodities`;
}

function updateTable(items) {
  const visible = items.slice(0, 150);
  els.table.innerHTML = visible
    .map(
      (item) => `
        <tr>
          <td class="num">${item.rank}</td>
          <td>${item.product}</td>
          <td>${item.packSize}</td>
          <td><span class="abc abc-${item.abcClass.toLowerCase()}">${item.abcClass}</span></td>
          <td class="num">${formatNumber(item.total)}</td>
          <td class="num">${formatNumber(item.averageMonthly)}</td>
          <td class="num">${item.activeMonths}</td>
          <td>${item.peakMonth}</td>
          <td class="num">${formatNumber(item.peakValue)}</td>
        </tr>
      `,
    )
    .join("");
  els.tableNote.textContent = `Showing ${formatNumber(visible.length)} of ${formatNumber(items.length)} filtered commodities`;
}

function updateCharts(items) {
  drawLineChart(els.monthlyChart, monthTotals(items));
  const topRows = items.slice(0, 10).map((item) => ({
    label: item.product,
    value: item.total,
    color: item.abcClass === "A" ? "#0f766e" : item.abcClass === "B" ? "#1d4ed8" : "#b7791f",
  }));
  drawBarChart(els.topChart, topRows, { horizontal: true, left: 170, bottom: 20 });
  drawAbcChart(els.abcChart, items);
}

function render() {
  const items = filteredData();
  updateKpis(items);
  updateCharts(items);
  updateTable(items);
}

function setupFilters() {
  const packs = [...new Set(data.commodities.map((item) => item.packSize))].sort((a, b) => a.localeCompare(b));
  els.packFilter.innerHTML = `<option value="all">All pack sizes</option>${packs
    .map((pack) => `<option value="${pack}">${pack}</option>`)
    .join("")}`;

  els.searchInput.addEventListener("input", (event) => {
    state.search = event.target.value;
    render();
  });
  els.packFilter.addEventListener("change", (event) => {
    state.pack = event.target.value;
    render();
  });
  els.abcFilter.addEventListener("change", (event) => {
    state.abc = event.target.value;
    render();
  });
  els.bandFilter.addEventListener("change", (event) => {
    state.band = event.target.value;
    render();
  });
  els.resetButton.addEventListener("click", () => {
    state.search = "";
    state.pack = "all";
    state.abc = "all";
    state.band = "all";
    els.searchInput.value = "";
    els.packFilter.value = "all";
    els.abcFilter.value = "all";
    els.bandFilter.value = "all";
    render();
  });
}

function downloadCsv() {
  const rows = filteredData();
  const headers = ["Rank", "Commodity", "Pack Size", "ABC Class", "Annual Total", "Average Monthly", "Active Months", "Peak Month", "Peak Quantity"];
  const body = rows.map((item) => [
    item.rank,
    item.product,
    item.packSize,
    item.abcClass,
    item.total,
    item.averageMonthly,
    item.activeMonths,
    item.peakMonth,
    item.peakValue,
  ]);
  const csv = [headers, ...body]
    .map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(","))
    .join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "nsccu-commodity-output.csv";
  link.click();
  URL.revokeObjectURL(link.href);
}

function init() {
  els.sourceFile.textContent = data.source.fileName;
  els.qualityNote.textContent = `${formatNumber(data.source.rawRows)} source rows were read from ${data.source.sheet}; ${formatNumber(
    data.source.namedCommodityRows,
  )} rows had named commodities and were aggregated into ${formatNumber(
    data.source.aggregatedCommodities,
  )} commodity-pack records. ${formatNumber(data.source.blankProductRows)} blank commodity-description rows were excluded from aggregation.`;
  setupFilters();
  els.downloadButton.addEventListener("click", downloadCsv);
  window.addEventListener("resize", render);
  render();
}

init();
