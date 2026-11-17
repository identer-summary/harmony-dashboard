(() => {
  "use strict";

  const initialNode = document.getElementById("initialReports");
  const reports = JSON.parse(initialNode?.textContent || "{}");
  const isDemoMode = document.body.dataset.demoMode === "true";

  let barChart = null;
  let detailChart = null;
  let currentOpenUnit = null;
  let currentFactTab = "noise";
  let toastTimer = null;

  const fallbackNoise = [70, 61, 45, 41, 43, 43, 34, 37, 37, 28, 19, 19, 21, 21, 37, 37, 45, 45, 32, 32, 25, 19, 48, 48, 39, 64, 64, 46, 46, 43, 25, 25, 25, 36, 36, 32, 30, 32, 32, 32, 34, 41, 41, 41, 41, 45, 70, 70, 79, 79, 30, 27, 21, 21, 23, 23, 21, 21, 19, 19];
  const fallbackVibration = [0.002, 0.002, 0.001, 0.001, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.001, 0.001, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.001, 0.001, 0.001, 0.001, 0.002, 0.002, 0.002, 0.001, 0.002, 0.001, 0.002, 0.002, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.002, 0.002, 0.002, 0.002, 0.002, 0.001, 0.001, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.002, 0.001];
  const fallbackTime = fallbackNoise.map((_, index) => `${index}초`);
  const fallbackFrequencyBins = [
    { hz: 0, count: 75 }, { hz: 20, count: 75 }, { hz: 40, count: 6 },
    { hz: 60, count: 4 }, { hz: 80, count: 6 }, { hz: 100, count: 4 },
    { hz: 120, count: 2 }, { hz: 140, count: 0 }, { hz: 160, count: 0 },
    { hz: 180, count: 0 }, { hz: 200, count: 0 }, { hz: 220, count: 0 },
    { hz: 240, count: 0 }, { hz: 260, count: 0 }, { hz: 280, count: 0 },
    { hz: 300, count: 0 }, { hz: 320, count: 0 }, { hz: 340, count: 0 },
    { hz: 360, count: 0 }, { hz: 380, count: 0 }, { hz: 400, count: 0 },
    { hz: 420, count: 2 }, { hz: 440, count: 0 }, { hz: 460, count: 2 },
  ];

  const measuredFactTabs = {
    noise: {
      tabId: "measuredTabNoise",
      title: "소음 변화 추이 (dB)",
      description: "600개 측정값을 1초 단위 최고값으로 정리했습니다.",
      ariaLabel: "60초 동안 측정한 소음 변화 그래프",
      metrics: [["측정 구간", "21:13:44–21:14:43"], ["데이터 포인트", "600개"], ["최고 소음", "79 dB"], ["57 dB 이상", "20회"]],
    },
    vibration: {
      tabId: "measuredTabVibration",
      title: "진동 변화 추이 (g)",
      description: "미세한 변화가 보이도록 0–0.002g 구간을 확대했습니다.",
      ariaLabel: "60초 동안 측정한 진동 변화 그래프",
      metrics: [["측정 구간", "21:13:44–21:14:43"], ["데이터 포인트", "600개"], ["평균 진동", "0.001 g"], ["최고 진동", "0.002 g"]],
    },
    frequency: {
      tabId: "measuredTabFrequency",
      title: "주파수 스펙트럼 분석 (Hz)",
      description: "감지된 주파수를 20Hz 구간별로 집계했습니다.",
      ariaLabel: "측정된 주파수를 20헤르츠 단위로 집계한 막대 그래프",
      metrics: [["감지 데이터", "176개"], ["주요 대역", "150 Hz 이하"], ["주요 대역 비율", "97.7%"], ["최고 주파수", "460 Hz"]],
    },
  };

  function byId(id) {
    return document.getElementById(id);
  }

  function statusFromNoise(noise) {
    if (noise >= 50) return "심각";
    if (noise >= 40) return "주의";
    return "양호";
  }

  function demoNoise(floor, line) {
    const baseline = 22 + ((floor * 7 + line * 5) % 13);
    if (line === 2 && floor === 13) return 42;
    if (line === 4 && floor === 15) return 51;
    return baseline;
  }

  function ensureDataForLine(line) {
    for (let floor = 1; floor <= 20; floor += 1) {
      const unit = `${floor}0${line}`;
      const key = `202-${unit}`;
      if (!reports[key]) {
        const maxNoise = demoNoise(floor, Number(line));
        reports[key] = {
          building: "202",
          unit,
          maxNoise,
          avgNoise: Math.max(maxNoise - 6, 0),
          vibration: maxNoise >= 40 ? 0.0011 : 0.0004,
          frequency: maxNoise >= 40 ? 140 : 220,
          status: statusFromNoise(maxNoise),
          source: "demo",
          time: "--:--:--",
        };
      }
    }
  }

  function setText(id, value) {
    const element = byId(id);
    if (element) element.textContent = value;
  }

  function formatValue(value, digits = 0) {
    const number = Number(value || 0);
    return Number.isFinite(number) ? number.toFixed(digits) : (0).toFixed(digits);
  }

  function showToast(message) {
    const toast = byId("toast");
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("is-visible");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => toast.classList.remove("is-visible"), 2800);
  }

  function updateTimestamp() {
    const now = new Date();
    setText("updateTime", now.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit", second: "2-digit" }));
  }

  function updateOverviewKpis(line) {
    const lineReports = [];
    for (let floor = 1; floor <= 20; floor += 1) {
      lineReports.push(reports[`202-${floor}0${line}`]);
    }

    const dangerCount = lineReports.filter((report) => report?.status === "심각").length;
    const warningCount = lineReports.filter((report) => report?.status === "주의").length;
    const loudest = lineReports.reduce((current, report) => {
      if (!current || Number(report?.maxNoise || 0) > Number(current.maxNoise || 0)) return report;
      return current;
    }, null);

    setText("dangerCount", dangerCount);
    setText("warningCount", warningCount);
    setText("maxNoiseKpi", formatValue(loudest?.maxNoise));
    setText("frequencyKpi", formatValue(loudest?.frequency || 0));
  }

  function renderGrid() {
    const line = byId("lineSelect").value;
    ensureDataForLine(line);
    setText("unitMapTitle", `202동 · ${line}호 라인`);
    setText("barChartTitle", `${line}호 라인 세대별 최고 소음`);

    const grid = byId("unitGrid");
    grid.innerHTML = "";

    for (let floor = 20; floor >= 1; floor -= 1) {
      const unit = `${floor}0${line}`;
      const key = `202-${unit}`;
      const data = reports[key];
      const button = document.createElement("button");
      const statusClass = data.status === "심각" ? "status-danger" : data.status === "주의" ? "status-warn" : "status-good";
      const sourceLabel = data.source === "demo" ? "예시값" : data.time || "실시간";

      button.type = "button";
      button.className = `unit-box ${statusClass}`;
      button.dataset.reportKey = key;
      button.setAttribute("aria-label", `${unit}호 ${data.status}, 최고 ${formatValue(data.maxNoise)}데시벨`);
      button.innerHTML = `<strong>${unit}호</strong><span>${data.status} · ${formatValue(data.maxNoise)}dB</span><small>${sourceLabel}</small>`;
      button.addEventListener("click", () => openReport(key));
      grid.appendChild(button);
    }

    updateOverviewKpis(line);
    updateBarChart(line);
    updateTimestamp();
  }

  function chartGrid() {
    return {
      color: "rgba(182, 255, 219, 0.08)",
      drawBorder: false,
    };
  }

  function chartTick() {
    return {
      color: "#758b81",
      font: { size: 9, family: "Pretendard, sans-serif" },
    };
  }

  function initGlobalCharts() {
    Chart.defaults.color = "#8fa49b";
    Chart.defaults.font.family = "Pretendard, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif";
    Chart.defaults.font.size = 9;

    new Chart(byId("typeChart"), {
      type: "doughnut",
      data: {
        labels: ["발망치·저주파", "가구 이동", "일반 생활소음"],
        datasets: [{
          data: [12, 4, 8],
          backgroundColor: ["#ff6f66", "#f7b955", "#62b5ff"],
          borderColor: "#0e1c17",
          borderWidth: 4,
          hoverOffset: 3,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "69%",
        plugins: {
          legend: { position: "bottom", labels: { boxWidth: 7, boxHeight: 7, usePointStyle: true, padding: 13 } },
          tooltip: { backgroundColor: "#172a22", padding: 10 },
        },
      },
    });

    new Chart(byId("timeChart"), {
      type: "bar",
      data: {
        labels: ["오전", "오후", "저녁", "야간"],
        datasets: [{
          data: [2, 1, 6, 15],
          backgroundColor: ["#40d98b", "#62b5ff", "#f7b955", "#b999ff"],
          borderRadius: 6,
          borderSkipped: false,
          barPercentage: 0.55,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { display: false }, ticks: chartTick(), border: { display: false } },
          y: { beginAtZero: true, suggestedMax: 16, grid: chartGrid(), ticks: { ...chartTick(), stepSize: 4 }, border: { display: false } },
        },
        plugins: { legend: { display: false }, tooltip: { backgroundColor: "#172a22", padding: 10 } },
      },
    });
  }

  function updateBarChart(line) {
    const labels = [];
    const values = [];
    const colors = [];

    for (let floor = 1; floor <= 20; floor += 1) {
      const report = reports[`202-${floor}0${line}`];
      labels.push(`${floor}0${line}`);
      values.push(Number(report?.maxNoise || 0));
      colors.push(report?.status === "심각" ? "#ff6f66" : report?.status === "주의" ? "#f7b955" : "#40d98b");
    }

    if (barChart) barChart.destroy();
    barChart = new Chart(byId("barChart"), {
      type: "bar",
      data: { labels, datasets: [{ data: values, backgroundColor: colors, borderRadius: 5, borderSkipped: false, barPercentage: 0.68 }] },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 250 },
        scales: {
          x: { grid: { display: false }, ticks: { ...chartTick(), maxRotation: 0, autoSkip: true, maxTicksLimit: 10 }, border: { display: false } },
          y: { beginAtZero: true, suggestedMax: 90, grid: chartGrid(), ticks: { ...chartTick(), stepSize: 20 }, border: { display: false } },
        },
        plugins: {
          legend: { display: false },
          tooltip: { backgroundColor: "#172a22", padding: 10, callbacks: { label: (context) => `최고 ${context.raw} dB` } },
        },
      },
    });
  }

  function reportPlot(data) {
    if (Array.isArray(data?.measurements) && data.measurements.length) {
      const frequencies = data.measurements.map((item) => Number(item.frequency || 0));
      return {
        noise: data.measurements.map((item) => Number(item.noise || 0)),
        vibration: data.measurements.map((item) => Number(item.vibration || 0)),
        frequency: frequencyHistogram(frequencies),
        time: data.measurements.map((item) => item.time || ""),
      };
    }
    return { noise: fallbackNoise, vibration: fallbackVibration, frequency: fallbackFrequencyBins, time: fallbackTime };
  }

  function frequencyHistogram(values) {
    const bins = Array.from({ length: 24 }, (_, index) => ({ hz: index * 20, count: 0 }));
    values.forEach((value) => {
      if (!Number.isFinite(value) || value <= 0) return;
      const index = Math.min(Math.floor(value / 20), bins.length - 1);
      bins[index].count += 1;
    });
    return bins;
  }

  function measuredGradient(context, stops) {
    const gradient = context.createLinearGradient(0, 0, 0, 330);
    stops.forEach(([offset, color]) => gradient.addColorStop(offset, color));
    return gradient;
  }

  function updateMeasuredFactCopy(tab) {
    const meta = measuredFactTabs[tab];
    setText("factChartTitle", meta.title);
    setText("factChartDescription", meta.description);
    meta.metrics.forEach(([label, value], index) => {
      setText(`factMetricLabel${index}`, label);
      setText(`factMetricValue${index}`, value);
    });

    const panel = byId("measuredTabPanel");
    panel.setAttribute("aria-labelledby", meta.tabId);
    byId("realDataChart").setAttribute("aria-label", meta.ariaLabel);
  }

  function renderDetailChart(data, tab = currentFactTab) {
    const plot = reportPlot(data);
    const canvas = byId("realDataChart");
    const context = canvas.getContext("2d");

    updateMeasuredFactCopy(tab);

    if (detailChart) detailChart.destroy();

    if (tab === "frequency") {
      detailChart = new Chart(canvas, {
        type: "bar",
        data: {
          labels: plot.frequency.map((item) => `${item.hz}Hz`),
          datasets: [{
            label: "감지 횟수",
            data: plot.frequency.map((item) => item.count),
            backgroundColor: plot.frequency.map((item) => item.hz <= 140 ? "#f4a048" : "#6f9ba4"),
            borderRadius: 5,
            borderSkipped: false,
            barPercentage: 0.72,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: { duration: 250 },
          scales: {
            x: { grid: { display: false }, ticks: { ...chartTick(), maxRotation: 0, autoSkip: true, maxTicksLimit: 7 }, border: { display: false } },
            y: { beginAtZero: true, suggestedMax: 75, grid: chartGrid(), ticks: { ...chartTick(), stepSize: 25 }, border: { display: false }, title: { display: true, text: "감지 횟수", color: "#647a70", font: { size: 8 } } },
          },
          plugins: { legend: { display: false }, tooltip: { backgroundColor: "#172a22", padding: 10 } },
        },
      });
      return;
    }

    const isNoise = tab === "noise";
    const values = isNoise ? plot.noise : plot.vibration;
    const stroke = isNoise
      ? measuredGradient(context, [[0, "#ff4b55"], [0.34, "#ffb22e"], [0.58, "#f2db35"], [1, "#42d884"]])
      : measuredGradient(context, [[0, "#e6ef5b"], [1, "#40d98b"]]);
    const fill = measuredGradient(context, isNoise
      ? [[0, "rgba(255,75,85,.46)"], [0.45, "rgba(242,219,53,.26)"], [1, "rgba(64,217,139,.08)"]]
      : [[0, "rgba(230,239,91,.28)"], [1, "rgba(64,217,139,.05)"]]);
    const datasets = [{
      label: isNoise ? "소음 (dB)" : "진동 (g)",
      data: values,
      borderColor: stroke,
      backgroundColor: fill,
      borderWidth: 2.4,
      pointRadius: 0,
      fill: true,
      tension: 0.22,
    }];

    if (isNoise) {
      datasets.push(
        { label: "심각 기준 57 dB", data: values.map(() => 57), borderColor: "#ff6f66", backgroundColor: "transparent", borderWidth: 1.2, borderDash: [7, 7], pointRadius: 0, fill: false, tension: 0 },
        { label: "주의 기준 39 dB", data: values.map(() => 39), borderColor: "#e0bc34", backgroundColor: "transparent", borderWidth: 1.2, borderDash: [7, 7], pointRadius: 0, fill: false, tension: 0 },
      );
    } else {
      datasets.push({ label: "참고 기준 0.002 g", data: values.map(() => 0.002), borderColor: "#e0bc34", backgroundColor: "transparent", borderWidth: 1.2, borderDash: [7, 7], pointRadius: 0, fill: false, tension: 0 });
    }

    detailChart = new Chart(canvas, {
      type: "line",
      data: { labels: plot.time, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 250 },
        interaction: { mode: "index", intersect: false },
        scales: {
          x: { grid: { display: false }, ticks: { ...chartTick(), maxTicksLimit: 5, maxRotation: 0 }, border: { display: false } },
          y: {
            beginAtZero: true,
            suggestedMax: isNoise ? 84 : 0.0024,
            grid: chartGrid(),
            ticks: { ...chartTick(), stepSize: isNoise ? 21 : 0.001, callback: (value) => isNoise ? value : Number(value).toFixed(3) },
            border: { display: false },
            title: { display: true, text: isNoise ? "소음 dB" : "진동 g", color: "#647a70", font: { size: 8 } },
          },
        },
        plugins: {
          legend: { display: false },
          tooltip: { backgroundColor: "#172a22", padding: 10, filter: (item) => item.datasetIndex === 0 },
        },
      },
    });
  }

  function updateReportContent(key) {
    const data = reports[key];
    if (!data) return;

    const building = data.building || "202";
    const unitNumber = Number.parseInt(data.unit, 10);
    const possibleImpactUnit = Number.isFinite(unitNumber) ? String(unitNumber + 100) : "확인 필요";
    const vibrationMg = Number(data.vibration || 0) * 1000;

    setText("targetUnit", `${building}동 ${data.unit}호`);
    setText("causeUnit", `${building}동 ${possibleImpactUnit}호`);
    setText("letterTo", `${building}동 ${possibleImpactUnit}호 거주자`);
    setText("dispMaxDb", `${formatValue(data.maxNoise)} dB`);
    setText("dispMaxVib", `${formatValue(vibrationMg, 2)} mg`);
    setText("dispFreq", `${formatValue(data.frequency)} Hz 이하`);
    setText("textMaxDb", formatValue(data.maxNoise));
    setText("textMaxVib", formatValue(vibrationMg, 2));
    setText("textFreq", formatValue(data.frequency));

    renderDetailChart(data);
  }

  function activateMeasuredFact(tab, shouldFocus = false) {
    if (!measuredFactTabs[tab]) return;
    currentFactTab = tab;

    document.querySelectorAll("[data-fact-tab]").forEach((button) => {
      const isActive = button.dataset.factTab === tab;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-selected", String(isActive));
      button.tabIndex = isActive ? 0 : -1;
      if (isActive && shouldFocus) button.focus();
    });

    renderDetailChart(reports[currentOpenUnit] || reports["202-503"], tab);
  }

  function moveMeasuredFactTab(event, index, buttons) {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const nextIndex = event.key === "Home"
      ? 0
      : event.key === "End"
        ? buttons.length - 1
        : (index + (event.key === "ArrowRight" ? 1 : -1) + buttons.length) % buttons.length;
    activateMeasuredFact(buttons[nextIndex].dataset.factTab, true);
  }

  function setActiveNav(action) {
    document.querySelectorAll(".nav-item").forEach((item) => {
      item.classList.toggle("is-active", item.dataset.action === action);
    });
  }

  function openReport(key) {
    currentOpenUnit = key;
    byId("dashboardView").classList.remove("is-active");
    byId("reportView").classList.add("is-active");
    setActiveNav("analysis");
    window.scrollTo({ top: 0, behavior: "smooth" });
    window.requestAnimationFrame(() => updateReportContent(key));
  }

  function closeReport() {
    currentOpenUnit = null;
    byId("reportView").classList.remove("is-active");
    byId("dashboardView").classList.add("is-active");
    setActiveNav("overview");
    window.scrollTo({ top: 0, behavior: "smooth" });
    renderGrid();
  }

  function closeSidebar() {
    document.body.classList.remove("sidebar-open");
    byId("menuToggle").setAttribute("aria-expanded", "false");
  }

  function handleNavigation(action) {
    closeSidebar();
    if (action === "analysis" || action === "incident") {
      openReport("202-503");
      return;
    }

    if (currentOpenUnit) closeReport();
    setActiveNav(action === "live" || action === "reports" ? action : "overview");

    if (action === "live") {
      byId("liveMonitoring").scrollIntoView({ behavior: "smooth", block: "start" });
    } else if (action === "reports") {
      byId("analyticsSection").scrollIntoView({ behavior: "smooth", block: "start" });
    } else if (action === "devices") {
      showToast("장치 관리 화면은 다음 개발 단계에서 연결됩니다.");
    } else if (action === "settings") {
      showToast("환경 설정 화면은 다음 개발 단계에서 연결됩니다.");
    } else {
      byId("overview").scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  function updateApprovalState() {
    byId("approveDraft").disabled = !(byId("factCheck").checked && byId("targetCheck").checked);
  }

  function attachEvents() {
    byId("lineSelect").addEventListener("change", renderGrid);
    byId("backToDashboard").addEventListener("click", closeReport);
    const measuredTabs = Array.from(document.querySelectorAll("[data-fact-tab]"));
    measuredTabs.forEach((button, index) => {
      button.addEventListener("click", () => activateMeasuredFact(button.dataset.factTab));
      button.addEventListener("keydown", (event) => moveMeasuredFactTab(event, index, measuredTabs));
    });
    document.querySelectorAll("[data-open-report]").forEach((button) => {
      button.addEventListener("click", () => openReport(button.dataset.openReport));
    });
    document.querySelectorAll("[data-action]").forEach((button) => {
      button.addEventListener("click", () => handleNavigation(button.dataset.action));
    });

    byId("menuToggle").addEventListener("click", () => {
      const isOpen = document.body.classList.toggle("sidebar-open");
      byId("menuToggle").setAttribute("aria-expanded", String(isOpen));
    });
    byId("sidebarScrim").addEventListener("click", closeSidebar);
    byId("closeDemoNotice").addEventListener("click", () => byId("demoNotice").remove());

    byId("factCheck").addEventListener("change", updateApprovalState);
    byId("targetCheck").addEventListener("change", updateApprovalState);
    byId("saveDraft").addEventListener("click", () => showToast("검토 상태가 이 브라우저에 임시 저장됐습니다."));
    byId("approveDraft").addEventListener("click", () => {
      const message = isDemoMode
        ? "검토 완료로 표시했습니다. 데모 모드이므로 실제 안내문은 발송되지 않았습니다."
        : "발송 연동 전 검토 완료 상태로 저장했습니다.";
      showToast(message);
    });
  }

  async function refreshReports() {
    try {
      const response = await fetch("/api/data", { headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      Object.assign(reports, await response.json());
      if (currentOpenUnit) {
        updateReportContent(currentOpenUnit);
      } else {
        renderGrid();
      }
    } catch (error) {
      console.warn("데이터 갱신을 잠시 후 다시 시도합니다.", error);
    }
  }

  window.addEventListener("DOMContentLoaded", () => {
    initGlobalCharts();
    attachEvents();
    renderGrid();
    window.setInterval(refreshReports, 5000);
  });
})();
