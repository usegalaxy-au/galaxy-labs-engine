// ============================================================================
// State Management
// ============================================================================

const state = {
  currentDays: 90,
  currentMetric: "visits",
  currentLab: "all",
  currentTool: "all",
  customDateRange: null,
};

// ============================================================================
// DOM Elements Cache
// ============================================================================

const elements = {
  loading: () => document.getElementById("loading"),
  noData: () => document.getElementById("nodata"),
  error: () => document.getElementById("error"),
  chart: () => document.getElementById("chart"),
  metricSelect: () => document.getElementById("metric-select"),
  labFilter: () => document.getElementById("lab-filter"),
  toolFilter: () => document.getElementById("tool-filter"),
  labFilterGroup: () => document.getElementById("lab-filter-group"),
  toolFilterGroup: () => document.getElementById("tool-filter-group"),
  startDate: () => document.getElementById("start-date"),
  endDate: () => document.getElementById("end-date"),
};

// ============================================================================
// UI State Functions
// ============================================================================

function showLoading() {
  elements.loading().style.display = "block";
  elements.error().style.display = "none";
  elements.chart().innerHTML = "";
}

function hideLoading() {
  elements.loading().style.display = "none";
}

function showError(message) {
  elements.error().textContent = `Failed to load data: ${message}`;
  elements.error().style.display = "block";
  hideLoading();
}

function showNoData() {
  elements.noData().style.display = "block";
  elements.chart().style.display = "none";
  hideLoading();
}

function hideNoData() {
  elements.noData().style.display = "none";
  elements.chart().style.display = "block";
}

// ============================================================================
// API Functions
// ============================================================================

function buildApiUrl() {
  let url = `/reporting/api/usage?metric=${state.currentMetric}`;

  if (state.customDateRange) {
    url += `&start_date=${state.customDateRange.start}`;
    url += `&end_date=${state.customDateRange.end}`;
  } else {
    url += `&days=${state.currentDays}`;
  }

  if (state.currentMetric === "tools") {
    url += `&lab=${state.currentLab}`;
    url += `&tool=${state.currentTool}`;
  }

  return url;
}

async function fetchChartData() {
  const url = buildApiUrl();
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

async function fetchToolsList() {
  const url = `/reporting/api/tools?lab=${state.currentLab}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

// ============================================================================
// Chart Rendering Functions
// ============================================================================

function calculateMaxY(traces) {
  let maxY = 0;
  traces.forEach((trace) => {
    const traceMax = Math.max(...trace.y);
    if (traceMax > maxY) {
      maxY = traceMax;
    }
  });
  return maxY;
}

function createChartElement(id, className = "lab-chart") {
  const chartDiv = document.createElement("div");
  chartDiv.className = className;
  chartDiv.id = id;
  return chartDiv;
}

function createChartTitle(text) {
  const titleDiv = document.createElement("div");
  titleDiv.className = "lab-chart-title fw-bold text-secondary";
  titleDiv.textContent = text;
  return titleDiv;
}

function renderVisitsChart(data) {
  const chartEl = elements.chart();

  if (data.traces.length === 0) {
    showNoData();
    return;
  }

  hideNoData();
  const maxY = calculateMaxY(data.traces);

  data.traces.forEach((trace, index) => {
    const chartId = `lab-chart-${index}`;
    const chartDiv = createChartElement(chartId);
    const titleText = trace.name.charAt(0).toUpperCase() + trace.name.substring(1);
    const titleDiv = createChartTitle(titleText);

    chartEl.appendChild(titleDiv);
    chartEl.appendChild(chartDiv);

    const layout = {
      xaxis: {
        type: "date",
        showticklabels: false,
      },
      yaxis: {
        range: [0, maxY],
        fixedrange: true,
      },
      hovermode: "closest",
      showlegend: false,
      margin: { l: 50, r: 20, t: 10, b: 20 },
    };

    const config = {
      responsive: true,
      displayModeBar: false,
      displaylogo: false,
    };

    const areaTrace = {
      ...trace,
      fill: "tozeroy",
      mode: "lines",
      line: { width: 1 },
    };

    Plotly.newPlot(chartId, [areaTrace], layout, config);
  });

  // Show x-axis labels on the last chart
  if (data.traces.length > 0) {
    const lastChartId = `lab-chart-${data.traces.length - 1}`;
    Plotly.relayout(lastChartId, {
      "xaxis.showticklabels": true,
      "margin.b": 40,
    });
  }
}

function renderToolsChart(data) {
  const chartEl = elements.chart();

  if (!data.traces[0] || data.traces[0].x.length === 0) {
    showNoData();
    return;
  }

  hideNoData();

  const chartId = "tool-chart";
  const chartDiv = createChartElement(chartId);
  chartDiv.style.height = "600px";
  chartEl.appendChild(chartDiv);

  const layout = {
    title: {
      text: `Tool runs over time${state.currentLab !== "all" ? " - " + state.currentLab : ""}`,
      font: { size: 20 },
    },
    xaxis: {
      title: "",
      type: "date",
    },
    yaxis: {
      title: "Number of jobs",
      rangemode: "tozero",
    },
    hovermode: "closest",
    showlegend: false,
    margin: { l: 60, r: 80, t: 80, b: 80 },
  };

  const config = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ["lasso2d", "select2d"],
    displaylogo: false,
  };

  Plotly.newPlot(chartId, data.traces, layout, config);
}

function renderChart(data) {
  if (state.currentMetric === "visits") {
    renderVisitsChart(data);
  } else if (state.currentMetric === "tools") {
    renderToolsChart(data);
  }
  // Add more metric types here as needed
}

// ============================================================================
// Main Data Loading Function
// ============================================================================

async function loadData() {
  showLoading();

  try {
    const data = await fetchChartData();
    renderChart(data);
    hideLoading();
  } catch (error) {
    console.error("Error loading data:", error);
    showError(error.message);
  }
}

async function loadToolsList() {
  try {
    const data = await fetchToolsList();
    const toolSelect = elements.toolFilter();

    toolSelect.innerHTML = '<option value="all">All</option>';

    data.tools.forEach((tool) => {
      const option = document.createElement("option");
      option.value = tool.tool_id;
      option.textContent = `${tool.display_name} (${tool.count})`;
      toolSelect.appendChild(option);
    });
  } catch (error) {
    console.error("Error loading tools list:", error);
  }
}

// ============================================================================
// Date Range Management
// ============================================================================

function applyPresetDateRange(days) {
  state.currentDays = days;
  state.customDateRange = null;
  elements.startDate().value = "";
  elements.endDate().value = "";
  loadData();
}

function applyCustomDateRange(startDate, endDate) {
  if (!startDate || !endDate) {
    alert("Please select both start and end dates");
    return;
  }

  state.customDateRange = { start: startDate, end: endDate };
  deactivateAllDateButtons();
  loadData();
}

function deactivateAllDateButtons() {
  document.querySelectorAll(".date-btn").forEach((btn) => {
    btn.classList.remove("active", "btn-primary");
    btn.classList.add("btn-outline-primary");
  });
}

function activateDateButton(button) {
  deactivateAllDateButtons();
  button.classList.remove("btn-outline-primary");
  button.classList.add("active", "btn-primary");
}

// ============================================================================
// Filter Management
// ============================================================================

function updateMetricFilters(metric) {
  const labFilterGroup = elements.labFilterGroup();
  const toolFilterGroup = elements.toolFilterGroup();

  if (metric === "tools") {
    labFilterGroup.style.display = "block";
    toolFilterGroup.style.display = "block";
    loadToolsList();
  } else {
    labFilterGroup.style.display = "none";
    toolFilterGroup.style.display = "none";
  }
}

// ============================================================================
// CSV Download
// ============================================================================

function buildDownloadUrl() {
  let url = `/reporting/api/download-csv?metric=${state.currentMetric}`;

  if (state.customDateRange) {
    url += `&start_date=${state.customDateRange.start}`;
    url += `&end_date=${state.customDateRange.end}`;
  } else {
    url += `&days=${state.currentDays}`;
  }

  if (state.currentMetric === "tools") {
    url += `&lab=${state.currentLab}`;
    url += `&tool=${state.currentTool}`;
  }

  return url;
}

function downloadCsv() {
  window.location.href = buildDownloadUrl();
}

// ============================================================================
// Event Listeners
// ============================================================================

function initializeEventListeners() {
  // Metric selection
  elements.metricSelect().addEventListener("change", (e) => {
    state.currentMetric = e.target.value;
    updateMetricFilters(state.currentMetric);
    loadData();
  });

  // Lab filter
  elements.labFilter().addEventListener("change", (e) => {
    state.currentLab = e.target.value;
    if (state.currentMetric === "tools") {
      loadToolsList();
    }
    loadData();
  });

  // Tool filter
  elements.toolFilter().addEventListener("change", (e) => {
    state.currentTool = e.target.value;
    loadData();
  });

  // Preset date range buttons
  document.querySelectorAll(".date-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      activateDateButton(e.target);
      const days = parseInt(e.target.dataset.days);
      applyPresetDateRange(days);
    });
  });

  // Custom date range
  document.getElementById("apply-custom-range").addEventListener("click", () => {
    const startDate = elements.startDate().value;
    const endDate = elements.endDate().value;
    applyCustomDateRange(startDate, endDate);
  });

  // CSV download
  document.getElementById("download-csv").addEventListener("click", downloadCsv);
}

// ============================================================================
// Initialization
// ============================================================================

function initialize() {
  initializeEventListeners();
  loadData();
}

// Start the application
initialize();
