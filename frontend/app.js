/**
 * AquaWatch MDP - Frontend Telemetry & Dashboard Controller
 * Connects directly to FastAPI backend endpoints:
 * - GET /health
 * - GET /api/readings/latest
 * - GET /api/readings?limit=30
 * - GET /api/alerts?limit=10
 * - GET /api/evaluate/latest
 */

const API_BASE = window.location.origin;

// Chart instance reference
let historicalChart = null;

// Initialize Chart.js
function initChart() {
  const ctx = document.getElementById('historicalChart').getContext('2d');
  
  historicalChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'pH Level',
          data: [],
          borderColor: '#38bdf8',
          backgroundColor: 'rgba(56, 189, 248, 0.1)',
          borderWidth: 2,
          tension: 0.35,
          yAxisID: 'y'
        },
        {
          label: 'Turbidity (NTU)',
          data: [],
          borderColor: '#f59e0b',
          backgroundColor: 'rgba(245, 158, 11, 0.1)',
          borderWidth: 2,
          tension: 0.35,
          yAxisID: 'y1'
        },
        {
          label: 'Temperature (°C)',
          data: [],
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          borderWidth: 2,
          tension: 0.35,
          yAxisID: 'y'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          labels: {
            color: '#9ca3af',
            font: { family: 'Plus Jakarta Sans', size: 11 }
          }
        },
        tooltip: {
          backgroundColor: '#111827',
          titleColor: '#f3f4f6',
          bodyColor: '#9ca3af',
          borderColor: '#1f293d',
          borderWidth: 1
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#6b7280', font: { family: 'JetBrains Mono', size: 10 } }
        },
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#38bdf8', font: { family: 'JetBrains Mono', size: 10 } },
          title: { display: true, text: 'pH / Temp (°C)', color: '#6b7280' }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          grid: { drawOnChartArea: false },
          ticks: { color: '#f59e0b', font: { family: 'JetBrains Mono', size: 10 } },
          title: { display: true, text: 'Turbidity (NTU)', color: '#f59e0b' }
        }
      }
    }
  });
}

// Format ISO date to local time HH:MM:SS
function formatTime(isoStr) {
  if (!isoStr) return '--';
  const d = new Date(isoStr);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

// Fetch System Health
async function fetchHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      document.getElementById('api-health-val').textContent = 'Healthy (200)';
      document.getElementById('api-health-val').className = 'meta-value status-good';
    } else {
      throw new Error();
    }
  } catch (err) {
    document.getElementById('api-health-val').textContent = 'Offline / Error';
    document.getElementById('api-health-val').className = 'meta-value status-critical';
  }
}

// Fetch and update latest readings and risk evaluation
async function fetchLatest() {
  try {
    const [readingRes, riskRes] = await Promise.all([
      fetch(`${API_BASE}/api/readings/latest`),
      fetch(`${API_BASE}/api/evaluate/latest`)
    ]);

    const reading = await readingRes.json();
    const risk = await riskRes.json();

    if (!reading) {
      document.getElementById('risk-status-text').textContent = 'AWAITING TELEMETRY';
      document.getElementById('risk-summary-text').textContent = 'No sensor readings currently stored in database. Start the simulator.';
      return;
    }

    // Provenance badge
    const badge = document.getElementById('source-badge');
    const badgeText = document.getElementById('source-text');
    if (reading.is_simulated) {
      badge.className = 'provenance-badge badge-simulated';
      badgeText.textContent = 'Simulated Telemetry';
      document.getElementById('node-type-val').textContent = 'Simulator Node';
    } else {
      badge.className = 'provenance-badge badge-hardware';
      badgeText.textContent = 'ESP32 Physical Node';
      document.getElementById('node-type-val').textContent = 'ESP32 Hardware';
    }

    document.getElementById('device-id-val').textContent = reading.device_id;
    document.getElementById('last-updated-val').textContent = formatTime(reading.timestamp);

    // Update Banner Risk Indicator
    const banner = document.getElementById('status-banner');
    const pulse = document.getElementById('risk-pulse');
    const statusText = document.getElementById('risk-status-text');
    const summaryText = document.getElementById('risk-summary-text');

    statusText.textContent = risk.overall_status;
    summaryText.textContent = risk.summary_message;

    banner.className = 'status-banner ' + (
      risk.overall_status === 'SAFE' ? 'status-safe' :
      risk.overall_status === 'WARNING' ? 'status-warning' :
      risk.overall_status === 'CRITICAL' ? 'status-critical' : ''
    );

    pulse.className = 'pulse-ring ' + (
      risk.overall_status === 'SAFE' ? 'pulse-safe' :
      risk.overall_status === 'WARNING' ? 'pulse-warning' :
      risk.overall_status === 'CRITICAL' ? 'pulse-critical' : ''
    );

    // Update Individual Parameter Cards
    // 1. pH
    if (reading.ph !== null && reading.ph !== undefined) {
      document.getElementById('val-ph').textContent = reading.ph.toFixed(2);
      const phPct = Math.min(100, Math.max(0, (reading.ph / 14) * 100));
      document.getElementById('fill-ph').style.width = `${phPct}%`;
      const phEval = risk.parameters_evaluated?.ph?.status || 'NORMAL';
      setBadge('badge-ph', phEval);
    } else {
      document.getElementById('val-ph').textContent = 'N/A';
      setBadge('badge-ph', 'UNINSTALLED');
    }

    // 2. Turbidity
    if (reading.turbidity !== null && reading.turbidity !== undefined) {
      document.getElementById('val-turbidity').textContent = reading.turbidity.toFixed(2);
      const turbPct = Math.min(100, Math.max(0, (reading.turbidity / 10) * 100));
      document.getElementById('fill-turbidity').style.width = `${turbPct}%`;
      const turbEval = risk.parameters_evaluated?.turbidity?.status || 'NORMAL';
      setBadge('badge-turbidity', turbEval);
    } else {
      document.getElementById('val-turbidity').textContent = 'N/A';
      setBadge('badge-turbidity', 'UNINSTALLED');
    }

    // 3. Temperature
    if (reading.temperature !== null && reading.temperature !== undefined) {
      document.getElementById('val-temp').textContent = reading.temperature.toFixed(1);
      const tempPct = Math.min(100, Math.max(0, (reading.temperature / 50) * 100));
      document.getElementById('fill-temp').style.width = `${tempPct}%`;
      const tempEval = risk.parameters_evaluated?.temperature?.status || 'NORMAL';
      setBadge('badge-temp', tempEval);
    } else {
      document.getElementById('val-temp').textContent = 'N/A';
      setBadge('badge-temp', 'UNINSTALLED');
    }

    // 4. Dissolved Oxygen
    if (reading.dissolved_oxygen !== null && reading.dissolved_oxygen !== undefined) {
      document.getElementById('val-do').textContent = reading.dissolved_oxygen.toFixed(2);
      const doPct = Math.min(100, Math.max(0, (reading.dissolved_oxygen / 12) * 100));
      document.getElementById('fill-do').style.width = `${doPct}%`;
      const doEval = risk.parameters_evaluated?.dissolved_oxygen?.status || 'NORMAL';
      setBadge('badge-do', doEval);
    } else {
      document.getElementById('val-do').textContent = 'N/A';
      setBadge('badge-do', 'UNINSTALLED');
    }

  } catch (err) {
    console.error('Error fetching latest telemetry:', err);
  }
}

function setBadge(elemId, status) {
  const el = document.getElementById(elemId);
  el.textContent = status;
  if (status === 'NORMAL' || status === 'SAFE') {
    el.style.color = 'var(--color-safe)';
    el.style.backgroundColor = 'var(--color-safe-bg)';
  } else if (status === 'WARNING') {
    el.style.color = 'var(--color-warning)';
    el.style.backgroundColor = 'var(--color-warning-bg)';
  } else if (status === 'CRITICAL') {
    el.style.color = 'var(--color-critical)';
    el.style.backgroundColor = 'var(--color-critical-bg)';
  } else {
    el.style.color = 'var(--text-dim)';
    el.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
  }
}

// Fetch historical readings for the line chart
async function fetchHistory() {
  try {
    const res = await fetch(`${API_BASE}/api/readings?limit=25`);
    const readings = await res.json();
    if (!readings || readings.length === 0) return;

    // Readings arrive desc (newest first). Reverse for chronological timeline
    const chronological = [...readings].reverse();

    const labels = chronological.map(r => formatTime(r.timestamp));
    const phData = chronological.map(r => r.ph);
    const turbData = chronological.map(r => r.turbidity);
    const tempData = chronological.map(r => r.temperature);

    if (historicalChart) {
      historicalChart.data.labels = labels;
      historicalChart.data.datasets[0].data = phData;
      historicalChart.data.datasets[1].data = turbData;
      historicalChart.data.datasets[2].data = tempData;
      historicalChart.update('none'); // smooth update without full reload
    }
  } catch (err) {
    console.error('Error fetching historical telemetry:', err);
  }
}

// Fetch recent threshold alerts
async function fetchAlerts() {
  try {
    const res = await fetch(`${API_BASE}/api/alerts?limit=10`);
    const alerts = await res.json();
    const container = document.getElementById('alerts-container');
    const countEl = document.getElementById('alert-count');

    countEl.textContent = alerts.length;

    if (!alerts || alerts.length === 0) {
      container.innerHTML = '<div class="empty-state">No active threshold alerts. Water parameters within normal bounds.</div>';
      return;
    }

    container.innerHTML = alerts.map(a => `
      <div class="alert-card severity-${a.severity}">
        <div class="alert-top">
          <span class="alert-param">${a.parameter} &bull; ${a.severity}</span>
          <span class="alert-time">${formatTime(a.timestamp)}</span>
        </div>
        <div class="alert-msg">${a.message}</div>
        <div class="alert-ref">Standard: ${a.standard_reference} (${a.threshold_limit})</div>
      </div>
    `).join('');
  } catch (err) {
    console.error('Error fetching alerts:', err);
  }
}

// Master refresh sequence
async function refreshDashboard() {
  await fetchHealth();
  await fetchLatest();
  await fetchHistory();
  await fetchAlerts();
}

// Bootstrapping
document.addEventListener('DOMContentLoaded', () => {
  initChart();
  refreshDashboard();

  // Periodic polling every 3 seconds for live monitoring
  setInterval(refreshDashboard, 3000);

  // Manual refresh button listener
  document.getElementById('btn-refresh').addEventListener('click', () => {
    refreshDashboard();
  });
});
