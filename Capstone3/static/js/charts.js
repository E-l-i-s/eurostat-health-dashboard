/**
 * charts.js - Austria Energy Transition Dashboard
 * ================================================
 * Professional redesign: no emoji-based renderers.
 * Pictogram replaced with paired donut charts (1970 vs 2024).
 * All chart options set for analyst-quality output.
 * Palette: muted, purposeful, high-contrast on white cards.
 */

'use strict';

/* ─── Colour Palette ──────────────────────────────────────── */
const C = {
  hydro:    '#0284C7',  // Sky Blue (water)
  wind:     '#0D9488',  // Teal (airy)
  solar:    '#F59E0B',  // Amber (sun)
  biomass:  '#65A30D',  // Lime (plants)
  nuclear:  '#6B7280',  // gray       (dormant)
  coal:     '#1F2937',  // Dark Gray (coal)
  gas:      '#7C3AED',  // Purple (gas)
  oil:      '#991B1B',  // Dark Red (oil)
  austria:  '#059669',
  eu:       '#4F46E5',  // indigo
  policy:   '#B45309',  // amber
  positive: '#059669',
  negative: '#B91C1C',
};

/* ─── Chart-wide defaults ─────────────────────────────────── */
Chart.defaults.font.family       = "Inter, -apple-system, 'Segoe UI', sans-serif";
Chart.defaults.font.size         = 11;
Chart.defaults.responsive        = true;
Chart.defaults.maintainAspectRatio = false;
Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15,23,42,0.92)';
Chart.defaults.plugins.tooltip.titleFont       = { size: 12, weight: '600' };
Chart.defaults.plugins.tooltip.bodyFont        = { size: 11 };
Chart.defaults.plugins.tooltip.padding         = 10;
Chart.defaults.plugins.tooltip.cornerRadius    = 6;
Chart.defaults.plugins.legend.labels.boxWidth  = 10;
Chart.defaults.plugins.legend.labels.padding   = 12;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.pointStyle    = 'rect';

/* ─── Chart instances ─────────────────────────────────────── */
let energyMixChart, renewableShareChart, co2DecadeChart, compareEuChart;
let mix1970Chart, mix2024Chart;
let renewableGrowthChart, intensityGdpChart, yoyChangeChart;

/* ─── D2 data cache - single fetch, reused ─────────────────── */
let _growthData = null, _intensityData = null, _heatmapData = null;
let _mixData = null, _annualData = null;

/* ─── Dual-range state ───────────────────────────────────── */
let minYear = 1900, maxYear = 2024;

/* ─── Utility ─────────────────────────────────────────────── */
async function api(path) {
  const r = await fetch('/api/' + path);
  if (!r.ok) throw new Error('HTTP ' + r.status + ' - /api/' + path);
  return r.json();
}

function destroy(inst) { if (inst) { try { inst.destroy(); } catch (_) {} } }

/* ─── Dual-handle Slider ─────────────────────────────────── */
function initSlider() {
  const minEl = document.getElementById('minYearSlider');
  const maxEl = document.getElementById('maxYearSlider');
  const minDsp = document.getElementById('minYearDisplay');
  const maxDsp = document.getElementById('maxYearDisplay');
  const fill   = document.getElementById('rangeFill');
  if (!minEl || !maxEl) return;

  function updateFill() {
    const span = 2024 - 1900;
    const l = ((minYear - 1900) / span) * 100;
    const r = ((maxYear - 1900) / span) * 100;
    if (fill) { fill.style.left = l + '%'; fill.style.width = (r - l) + '%'; }
  }

  minEl.addEventListener('input', () => {
    minYear = +minEl.value;
    if (minYear >= maxYear) { minYear = maxYear - 1; minEl.value = minYear; }
    minDsp.textContent = minYear;
    updateFill();
    clearTimeout(minEl._t);
    minEl._t = setTimeout(refreshMix, 200);
  });

  maxEl.addEventListener('input', () => {
    maxYear = +maxEl.value;
    if (maxYear <= minYear) { maxYear = minYear + 1; maxEl.value = maxYear; }
    maxDsp.textContent = maxYear;
    updateFill();
    clearTimeout(maxEl._t);
    maxEl._t = setTimeout(refreshMix, 200);
  });

  updateFill();
}

function getActiveSources() {
  return Array.from(document.querySelectorAll('#sourceToggles input:checked')).map(b => b.value);
}

/* ─── RENDER: Energy Mix stacked area ───────────────────────── */
function renderEnergyMix(data) {
  const ctx = document.getElementById('energyMixChart');
  if (!ctx) return;
  destroy(energyMixChart);

  const active = getActiveSources();
  const srcMap = [
    { key: 'hydro',   label: 'Hydro'   },
    { key: 'wind',    label: 'Wind'    },
    { key: 'solar',   label: 'Solar'   },
    { key: 'biomass', label: 'Biomass' },
    { key: 'coal',    label: 'Coal'    },
    { key: 'gas',     label: 'Gas'     },
    { key: 'oil',     label: 'Oil'     },
  ];

  const years = data.map(d => d.year);
  const datasets = srcMap
    .filter(s => active.includes(s.key))
    .map(s => ({
      label:           s.label,
      data:            data.map(d => +(d[s.key + '_twh'] || 0).toFixed(1)),
      backgroundColor: C[s.key] + 'B0',
      borderColor:     C[s.key],
      borderWidth:     0.5,
      fill:            true,
      tension:         0.25,
      pointRadius:     0,
    }));

  energyMixChart = new Chart(ctx, {
    type: 'line',
    data: { labels: years, datasets },
    options: {
      plugins: {
        legend:     { position: 'bottom' },
        tooltip:    { mode: 'index', intersect: false },
        annotation: { annotations: {} },
      },
      scales: {
        x: {
          title: { display: false },
          ticks: {
            maxTicksLimit: 13,
            callback: (v, i) => years[i] ?? '',
            maxRotation: 0,
          },
          grid: { color: '#F1F5F9' },
        },
        y: {
          stacked:     true,
          title:       { display: true, text: 'TWh', font: { size: 10 } },
          beginAtZero: true,
          grid:        { color: '#F1F5F9' },
        },
      },
      interaction: { mode: 'nearest', axis: 'x', intersect: false },
    },
  });
}

async function refreshMix() {
  if (!_mixData) return;
  const filtered = _mixData.filter(d => d.year >= minYear && d.year <= maxYear);
  renderEnergyMix(filtered);
}

/* ─── RENDER: Renewable Share with policy annotations ───────── */
function renderRenewableShare(data) {
  const ctx = document.getElementById('renewableShareChart');
  if (!ctx) return;
  destroy(renewableShareChart);

  /* Build annotation objects */
  const annotations = {};

  (data.policies || []).forEach(p => {
    const idx = data.years.indexOf(p.year);
    if (idx < 0) return;
    annotations['pol_' + p.year] = {
      type:        'line',
      xMin:        idx, xMax: idx,
      borderColor: C.policy + '99',
      borderWidth: 1.5,
      borderDash:  [4, 4],
      label: {
        display:         true,
        content:         String(p.year),
        position:        'start',
        backgroundColor: C.policy,
        color:           '#fff',
        font:            { size: 9, weight: '600' },
        padding:         { x: 4, y: 2 },
        yAdjust:         -10,
      },
    };
  });

  /* Zwentendorf nuclear referendum - point annotation */
  const zwIdx = data.years.indexOf(1978);
  if (zwIdx >= 0) {
    annotations['zwentendorf'] = {
      type:            'point',
      xValue:          zwIdx,
      yValue:          data.shares[zwIdx],
      backgroundColor: '#1D4ED8',
      radius:          5,
      borderColor:     '#fff',
      borderWidth:     2,
      label: {
        display:         true,
        content:         ['1978 referendum', 'Zero nuclear - permanent'],
        position:        'top',
        backgroundColor: '#1D4ED8',
        color:           '#fff',
        font:            { size: 9 },
        padding:         { x: 6, y: 3 },
      },
    };
  }

  renewableShareChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.years,
      datasets: [{
        label:           'Renewable share (%)',
        data:            data.shares,
        borderColor:     C.austria,
        backgroundColor: C.austria + '14',
        fill:            true,
        tension:         0.2,
        pointRadius:     0,
        borderWidth:     2,
      }],
    },
    options: {
      plugins: {
        legend:     { display: false },
        tooltip:    { mode: 'index', intersect: false },
        annotation: { annotations },
      },
      scales: {
        x: {
          ticks: {
            maxTicksLimit: 13,
            callback: (v, i) => data.years[i] ?? '',
            maxRotation: 0,
          },
          grid: { color: '#F1F5F9' },
        },
        y: {
          title:  { display: true, text: '% gross final energy', font: { size: 10 } },
          min: 0, max: 65,
          grid: { color: '#F1F5F9' },
        },
      },
      interaction: { mode: 'nearest', axis: 'x', intersect: false },
    },
  });
}

/* ─── RENDER: Policy Timeline ────────────────────────────────── */
const POLICY_DESCRIPTIONS = {
  1918: 'End of WWI - reconstruction',
  1945: 'End of WWII - infrastructure rebuild',
  1955: 'State Treaty - economic growth begins',
  1978: 'Zwentendorf referendum - zero nuclear',
  1995: 'EU accession - energy market alignment',
  2002: 'Ökostromergesetz - feed-in tariffs',
  2007: 'Climate & Energy Strategy (#mission2030)',
  2011: 'Energy Transition Act (Energiewende)',
  2018: 'Austrian Climate and Energy Plan (IEKP)',
  2021: 'Renewable Expansion Act (EAG) - 100% by 2030',
  2024: 'Net-zero 2040 commitment confirmed',
};

function renderPolicyTimeline(policies) {
  const el = document.getElementById('policyTimeline');
  if (!el) return;
  el.innerHTML = policies.map(p => {
    const desc = POLICY_DESCRIPTIONS[p.year] || p.event_name;
    return `
      <div class="timeline-node" title="${p.event_name}">
        <div class="timeline-dot"></div>
        <div class="timeline-yr">${p.year}</div>
        <div class="timeline-evt">${desc}</div>
      </div>`;
  }).join('');
}

/* ─── RENDER: CO₂ by Decade ──────────────────────────────── */
function renderCo2Decade(data) {
  const ctx = document.getElementById('co2DecadeChart');
  if (!ctx) return;
  destroy(co2DecadeChart);

  const maxVal = Math.max(...data.values);

  co2DecadeChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [{
        label:           'CO₂ (Mt)',
        data:            data.values,
        backgroundColor: data.values.map(v => {
          const t = v / maxVal;
          // Darker blue for higher decades (co2 growth), lighter for drop
          const r = Math.round(29 + t * 30);
          const g = Math.round(78 + t * 20);
          const b = Math.round(216 - t * 60);
          return `rgba(${r},${g},${b},0.85)`;
        }),
        borderRadius:    4,
        borderSkipped:   false,
      }],
    },
    options: {
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: c => c.parsed.y.toFixed(1) + ' Mt CO₂ (total for decade)',
          },
        },
        annotation: { annotations: {} },
      },
      scales: {
        x: { grid: { display: false } },
        y: {
          title:       { display: true, text: 'Total CO₂ (Mt)', font: { size: 10 } },
          beginAtZero: true,
          grid:        { color: '#F1F5F9' },
        },
      },
    },
  });
}

/* ─── RENDER: EU Comparison ──────────────────────────────── */
function renderCompareEu(data) {
  const ctx = document.getElementById('compareEuChart');
  if (!ctx) return;
  destroy(compareEuChart);

  const years  = data.austria.map(d => d.year);
  const atVals = data.austria.map(d => d.renewable_share);
  const euVals = data.eu_average.map(d => d.renewable_share);

  compareEuChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: years,
      datasets: [
        {
          label:           'Austria',
          data:            atVals,
          borderColor:     C.austria,
          backgroundColor: C.austria + '14',
          fill:            true,
          tension:         0.2,
          pointRadius:     0,
          borderWidth:     2,
        },
        {
          label:           'EU27 Average',
          data:            euVals,
          borderColor:     C.eu,
          backgroundColor: 'transparent',
          fill:            false,
          tension:         0.2,
          pointRadius:     0,
          borderWidth:     1.5,
          borderDash:      [5, 4],
        },
      ],
    },
    options: {
      plugins: {
        legend:     { position: 'bottom' },
        tooltip:    { mode: 'index', intersect: false },
        annotation: { annotations: {} },
      },
      scales: {
        x: {
          ticks: { maxTicksLimit: 8, maxRotation: 0 },
          grid:  { color: '#F1F5F9' },
        },
        y: {
          title: { display: true, text: '% gross final energy', font: { size: 10 } },
          min: 0, max: 60,
          grid: { color: '#F1F5F9' },
        },
      },
      interaction: { mode: 'nearest', axis: 'x', intersect: false },
    },
  });
}

/* ─── RENDER: KPI Cards ──────────────────────────────────── */
function renderKpi(data) {
  const set = (id, v) => { const e = document.getElementById(id); if (e) e.textContent = v; };
  set('kpiShare',       (data.current_renewable_share || 0).toFixed(1) + '%');
  set('kpiCo2',         '−' + Math.abs(data.co2_reduction_pct || 0).toFixed(1) + '%');
  set('kpiIntensity',   '−' + Math.abs(data.energy_intensity_change || 0).toFixed(1) + '%');
  set('kpiRenewableTwh', (data.current_renewable_twh || 0).toFixed(0) + ' TWh');
}

/* ─── RENDER: Mix Comparison Donuts (replaces pictogram) ─────── */
function renderMixDonut(canvasId, row, titleYear) {
  const ctx = document.getElementById(canvasId);
  if (!ctx || !row) return;

  const srcs = ['hydro','wind','solar','biomass','coal','gas','oil'];
  const lbls = ['Hydro','Wind','Solar','Biomass','Coal','Gas','Oil'];
  const vals = srcs.map(s => Math.max(0, +(row[s + '_twh'] || 0).toFixed(1)));
  const cols = srcs.map(s => C[s]);
  const total = vals.reduce((a, b) => a + b, 0);

  const inst = canvasId === 'mix1970Chart' ? mix1970Chart : mix2024Chart;
  destroy(inst);

  const chart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels:   lbls,
      datasets: [{
        data:            vals,
        backgroundColor: cols,
        borderColor:     '#fff',
        borderWidth:     2,
        hoverOffset:     6,
      }],
    },
    options: {
      cutout: '62%',
      plugins: {
        legend: { position: 'right', labels: { boxWidth: 10, padding: 8, font: { size: 10 } } },
        tooltip: {
          callbacks: {
            label: c => {
              const pct = total > 0 ? ((c.parsed / total) * 100).toFixed(1) : 0;
              return ` ${c.label}: ${c.parsed.toFixed(1)} TWh (${pct}%)`;
            },
          },
        },
        annotation: { annotations: {} },
      },
    },
    plugins: [{
      id: 'centreLabel',
      afterDraw(chart) {
        const { ctx, chartArea: { top, left, right, bottom } } = chart;
        const cx = (left + right) / 2;
        const cy = (top + bottom) / 2;
        ctx.save();
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = '#0F172A';
        ctx.font = '700 14px Inter, sans-serif';
        ctx.fillText(titleYear, cx, cy - 8);
        ctx.fillStyle = '#94A3B8';
        ctx.font = '400 10px Inter, sans-serif';
        ctx.fillText(total.toFixed(0) + ' TWh', cx, cy + 9);
        ctx.restore();
      },
    }],
  });

  if (canvasId === 'mix1970Chart') mix1970Chart = chart;
  else mix2024Chart = chart;
}

/* ─── RENDER: Renewable Source Growth ───────────────────────── */
function renderRenewableGrowth(data, srcFilter) {
  const ctx = document.getElementById('renewableGrowthChart');
  if (!ctx) return;
  destroy(renewableGrowthChart);

  const srcs = ['hydro','wind','solar','biomass'];
  const lbls = ['Hydro','Wind','Solar','Biomass'];

  const datasets = srcs.map((s, i) => ({
    label:           lbls[i],
    data:            (data[s] || []).map(v => +v.toFixed(2)),
    borderColor:     C[s],
    backgroundColor: C[s] + '12',
    fill:            true,
    tension:         0.3,
    pointRadius:     0,
    borderWidth:     1.8,
    hidden:          srcFilter !== 'all' && s !== srcFilter,
  }));

  renewableGrowthChart = new Chart(ctx, {
    type: 'line',
    data: { labels: data.years, datasets },
    options: {
      plugins: {
        legend:     { position: 'bottom' },
        tooltip:    { mode: 'index', intersect: false },
        annotation: { annotations: {} },
      },
      scales: {
        x: {
          ticks: { maxTicksLimit: 13, maxRotation: 0 },
          grid:  { color: '#F1F5F9' },
        },
        y: {
          title:       { display: true, text: 'TWh', font: { size: 10 } },
          beginAtZero: true,
          grid:        { color: '#F1F5F9' },
        },
      },
      interaction: { mode: 'nearest', axis: 'x', intersect: false },
    },
  });
}

/* ─── RENDER: Intensity vs GDP (bubble) ──────────────────────── */
function renderIntensityGdp(data, metric, decFilter) {
  const ctx = document.getElementById('intensityGdpChart');
  if (!ctx) return;
  destroy(intensityGdpChart);

  let pts = data.datapoints || [];
  if (decFilter && decFilter !== 'all') {
    pts = pts.filter(p => Math.floor(p.year / 10) * 10 + 's' === decFilter);
  }
  if (!pts.length) return;

  const yField = metric === 'co2' ? 'co2_per_capita' : 'energy_intensity';
  const yLabel = metric === 'co2' ? 'CO₂ per capita (t)' : 'Energy intensity (TWh / B USD GDP)';

  const maxC = Math.max(...pts.map(p => p.total_consumption || 0), 1);
  const minC = Math.min(...pts.map(p => p.total_consumption || 0), 0);
  const span = maxC - minC || 1;

  intensityGdpChart = new Chart(ctx, {
    type: 'bubble',
    data: {
      datasets: [{
        label:           yLabel,
        data:            pts.map(p => ({
          x: p.gdp_per_capita,
          y: p[yField] || 0,
          r: Math.max(3, ((p.total_consumption - minC) / span) * 12 + 3),
        })),
        backgroundColor: pts.map(p => {
          const t = (p.year - 1900) / 124;
          // Dark-to-light: early years dark blue, recent years teal
          return `rgba(${Math.round(29 + t * 26)},${Math.round(78 + t * 130)},${Math.round(216 - t * 66)},0.55)`;
        }),
        borderColor:     pts.map(() => '#1D4ED830'),
        borderWidth:     1,
      }],
    },
    options: {
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: c => {
              const p = pts[c.dataIndex];
              return [
                `${p.year}`,
                `GDP/capita: $${p.gdp_per_capita.toLocaleString()}`,
                `${yLabel}: ${(p[yField] || 0).toFixed(2)}`,
                `TPES: ${(p.total_consumption || 0).toFixed(0)} TWh`,
              ];
            },
          },
        },
        annotation: { annotations: {} },
      },
      scales: {
        x: {
          type:  'logarithmic',
          title: { display: true, text: 'GDP per capita (USD, log scale)', font: { size: 10 } },
          grid:  { color: '#F1F5F9' },
        },
        y: {
          title:       { display: true, text: yLabel, font: { size: 10 } },
          beginAtZero: true,
          grid:        { color: '#F1F5F9' },
        },
      },
    },
  });
}

/* ─── RENDER: Heatmap (column-normalised, single-hue blue) ──── */
function renderHeatmap(data) {
  const container = document.getElementById('heatmapContainer');
  if (!container) return;

  const { sources, decades, values } = data;

  /* Column-wise max (per source) - prevents scale distortion across sources */
  const colMax = sources.map((_, si) =>
    Math.max(...values.map(row => row[si] || 0), 0.001)
  );

  /* Build table */
  let html = '<table class="heatmap-table"><thead><tr>';
  html += '<th class="row-header">Decade</th>';
  sources.forEach(s => { html += `<th>${s.charAt(0).toUpperCase() + s.slice(1)}</th>`; });
  html += '</tr></thead><tbody>';

  decades.forEach((dec, ri) => {
    html += `<tr><td class="decade-label">${dec}</td>`;
    values[ri].forEach((val, ci) => {
      const t   = colMax[ci] > 0 ? val / colMax[ci] : 0;
      /* Single-hue blue ramp: #EFF6FF (low) → #1D4ED8 (high) */
      const r   = Math.round(239 - t * (239 - 29));
      const g   = Math.round(246 - t * (246 - 78));
      const b   = Math.round(255 - t * (255 - 216));
      const txt = t > 0.55 ? '#fff' : '#1E293B';
      html += `<td style="background:rgb(${r},${g},${b});color:${txt};min-width:46px" title="${sources[ci]}: ${val.toFixed(1)} TWh avg">${val.toFixed(1)}</td>`;
    });
    html += '</tr>';
  });

  html += '</tbody></table>';
  container.innerHTML = html;
}

/* ─── RENDER: YoY Change ─────────────────────────────────── */
function renderYoyChange(mixData, decFilter) {
  const ctx = document.getElementById('yoyChangeChart');
  if (!ctx) return;
  destroy(yoyChangeChart);

  let rows = mixData || [];
  if (decFilter && decFilter !== 'all') {
    rows = rows.filter(d => Math.floor(d.year / 10) * 10 + 's' === decFilter);
  }
  if (rows.length < 2) return;

  const last2 = rows.slice(-2);
  const srcs  = ['hydro_twh','wind_twh','solar_twh','biomass_twh','coal_twh','gas_twh','oil_twh'];
  const names = ['Hydro','Wind','Solar','Biomass','Coal','Gas','Oil'];
  const ks    = ['hydro','wind','solar','biomass','coal','gas','oil'];
  const diffs = srcs.map(k => +((last2[1][k] || 0) - (last2[0][k] || 0)).toFixed(2));

  yoyChangeChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: names,
      datasets: [{
        label:           `Change ${last2[0].year}→${last2[1].year} (TWh)`,
        data:            diffs,
        backgroundColor: diffs.map((v, i) => v >= 0 ? C[ks[i]] + 'CC' : C.negative + 'CC'),
        borderRadius:    4,
        borderSkipped:   false,
      }],
    },
    options: {
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: c => (c.parsed.y >= 0 ? '+' : '') + c.parsed.y.toFixed(2) + ' TWh',
          },
        },
        annotation: { annotations: {} },
      },
      scales: {
        x: { grid: { display: false } },
        y: {
          title: { display: true, text: 'TWh change', font: { size: 10 } },
          grid:  { color: '#F1F5F9' },
        },
      },
    },
  });
}

/* ─── RENDER: SVG Sankey (energy flow diagram) ───────────────── */
function renderSankey(data) {
  const container = document.getElementById('sankeyContainer');
  if (!container || !data || !data.flows) return;

  const W = 640, H = 280, PAD = 14;
  const SRCS = ['Hydro','Wind','Solar','Biomass','Coal','Gas','Oil'];
  const DEMS = ['Electricity','Heating','Transport'];
  const srcCol = { Hydro:C.hydro, Wind:C.wind, Solar:C.solar, Biomass:C.biomass, Coal:C.coal, Gas:C.gas, Oil:C.oil };
  const demCol = { Electricity:'#0F172A', Heating:'#B45309', Transport:'#4F46E5' };

  const flowMap = {};
  data.flows.forEach(([s, d, v]) => { flowMap[`${s}|${d}`] = (flowMap[`${s}|${d}`] || 0) + v; });

  const srcTot = {}, demTot = {};
  Object.entries(flowMap).forEach(([k, v]) => {
    const [s, d] = k.split('|');
    srcTot[s] = (srcTot[s] || 0) + v;
    demTot[d] = (demTot[d] || 0) + v;
  });

  const grand = Object.values(srcTot).reduce((a,b) => a+b, 0) || 1;
  const useH  = H - PAD * 2;
  const nW    = 14, sX = 42, dX = W - 56;

  /* Source node layout */
  let sy = PAD;
  const sY = {};
  SRCS.forEach(s => {
    const h = Math.max(5, (srcTot[s] || 0) / grand * useH);
    sY[s] = { y: sy, h };
    sy += h + 3;
  });

  /* Demand node layout */
  let dy = PAD;
  const dY = {};
  DEMS.forEach(d => {
    const h = Math.max(5, (demTot[d] || 0) / grand * useH);
    dY[d] = { y: dy, h };
    dy += h + 10;
  });

  const sCursor = {}, dCursor = {};
  SRCS.forEach(s => { sCursor[s] = sY[s]?.y || 0; });
  DEMS.forEach(d => { dCursor[d] = dY[d]?.y || 0; });

  let paths = '', nodes = '', labels = '';
  const mx = (sX + nW + dX) / 2;

  /* Flows */
  Object.entries(flowMap).forEach(([k, v]) => {
    const [s, d] = k.split('|');
    if (!sY[s] || !dY[d]) return;
    const fh = Math.max(1.5, (v / grand) * useH);
    const y0 = sCursor[s] + fh / 2;
    const y1 = dCursor[d] + fh / 2;
    sCursor[s] += fh + 0.5;
    dCursor[d] += fh + 0.5;
    paths += `<path d="M${sX+nW},${y0} C${mx},${y0} ${mx},${y1} ${dX},${y1}"
      stroke="${srcCol[s] || '#94A3B8'}" stroke-width="${Math.max(1.2, fh)}"
      fill="none" opacity="0.35"/>`;
  });

  /* Source nodes */
  SRCS.forEach(s => {
    const n = sY[s];
    if (!n) return;
    nodes  += `<rect x="${sX}" y="${n.y}" width="${nW}" height="${n.h}" rx="2" fill="${srcCol[s]}"/>`;
    labels += `<text x="${sX-5}" y="${n.y + n.h/2 + 3.5}" text-anchor="end" font-size="9.5" fill="#475569" font-family="Inter,sans-serif">${s}</text>`;
  });

  /* Demand nodes */
  DEMS.forEach(d => {
    const n = dY[d];
    if (!n) return;
    nodes  += `<rect x="${dX}" y="${n.y}" width="${nW}" height="${n.h}" rx="2" fill="${demCol[d]}"/>`;
    labels += `<text x="${dX+nW+5}" y="${n.y + n.h/2 + 3.5}" text-anchor="start" font-size="9.5" fill="#475569" font-family="Inter,sans-serif">${d}</text>`;
  });

  labels += `<text x="${W/2}" y="${H-2}" text-anchor="middle" font-size="9" fill="#94A3B8" font-family="Inter,sans-serif">
    2024 - flow widths proportional to TWh · Source: IEA Austria Energy Balance 2023
  </text>`;

  container.innerHTML = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;min-width:480px">
    ${paths}${nodes}${labels}
  </svg>`;
}

/* ─── Data Table ─────────────────────────────────────────── */
let _tblData = [], _tblPage = 1, _sortCol = 'year', _sortAsc = true;
const PG = 20;

function renderTable(decade, search) {
  const body    = document.getElementById('tableBody');
  const info    = document.getElementById('pageInfo');
  const prevBtn = document.getElementById('prevPage');
  const nextBtn = document.getElementById('nextPage');
  if (!body) return;

  let rows = [..._tblData];
  if (decade && decade !== 'all') rows = rows.filter(r => r.decade === decade);
  if (search) {
    const q = search.toLowerCase();
    rows = rows.filter(r =>
      String(r.year).includes(q) ||
      (r.energy_source || '').toLowerCase().includes(q) ||
      (r.decade || '').toLowerCase().includes(q)
    );
  }

  rows.sort((a, b) => {
    let av = a[_sortCol], bv = b[_sortCol];
    if (typeof av === 'string') av = av.toLowerCase();
    if (typeof bv === 'string') bv = bv.toLowerCase();
    return _sortAsc ? (av < bv ? -1 : av > bv ? 1 : 0) : (av > bv ? -1 : av < bv ? 1 : 0);
  });

  const totalPg = Math.max(1, Math.ceil(rows.length / PG));
  _tblPage = Math.min(_tblPage, totalPg);
  const slice = rows.slice((_tblPage - 1) * PG, _tblPage * PG);

  if (!slice.length) {
    body.innerHTML = '<tr><td colspan="10" style="text-align:center;padding:24px;color:#94A3B8">No records match the current filters.</td></tr>';
  } else {
    body.innerHTML = slice.map(r => {
      const badge = (r.renewable_share_pct || 0) >= 30
        ? `<span class="renewable-badge">${(r.renewable_share_pct||0).toFixed(1)}%</span>`
        : `${(r.renewable_share_pct||0).toFixed(1)}%`;
      return `<tr>
        <td class="yr-cell">${r.year}</td>
        <td>${r.decade || '-'}</td>
        <td style="text-transform:capitalize">${r.energy_source || '-'}</td>
        <td>${(r.total_energy_consumption_twh||0).toFixed(1)}</td>
        <td>${badge}</td>
        <td>${(r.co2_emissions_mt||0).toFixed(2)}</td>
        <td>${(r.co2_per_capita_t||0).toFixed(2)}</td>
        <td>${(r.hydro_twh||0).toFixed(1)}</td>
        <td>${(r.wind_twh||0).toFixed(2)}</td>
        <td>${(r.solar_twh||0).toFixed(2)}</td>
      </tr>`;
    }).join('');
  }

  info.textContent = `${rows.length} records · page ${_tblPage} of ${totalPg}`;
  prevBtn.disabled = _tblPage <= 1;
  nextBtn.disabled = _tblPage >= totalPg;

  prevBtn.onclick = () => { _tblPage--; renderTable(decade, search); };
  nextBtn.onclick = () => { _tblPage++; renderTable(decade, search); };
}

/* ─── Dashboard 1 initialisation ─────────────────────────── */
async function initDashboard1() {
  try {
    const [shareData, co2Data, kpiData, euData, mixAll] = await Promise.all([
      api('renewable_share'),
      api('co2_decade'),
      api('kpi_summary'),
      api('compare_eu?min_year=1990&max_year=2024'),
      api('energy_mix?min_year=1900&max_year=2024'),
    ]);

    _mixData = mixAll;

    renderEnergyMix(mixAll);
    renderRenewableShare(shareData);
    renderCo2Decade(co2Data);
    renderKpi(kpiData);
    renderCompareEu(euData);
    renderPolicyTimeline(shareData.policies || []);

    /* Mix comparison donuts (replaces pictogram) */
    const row1970 = mixAll.find(d => d.year === 1970) || mixAll[0];
    const row2024 = mixAll.find(d => d.year === 2024) || mixAll[mixAll.length - 1];
    renderMixDonut('mix1970Chart', row1970, '1970');
    renderMixDonut('mix2024Chart', row2024, '2024');

  } catch (e) { console.error('[D1 error]', e); }

  /* Wire slider */
  initSlider();

  /* Wire source toggles */
  document.querySelectorAll('#sourceToggles input').forEach(cb =>
    cb.addEventListener('change', () => _mixData && renderEnergyMix(
      _mixData.filter(d => d.year >= minYear && d.year <= maxYear)
    ))
  );
}

/* ─── Dashboard 2 initialisation ─────────────────────────── */
async function initDashboard2() {
  try {
    const [growthData, intensityData, heatmapData, mixAll, annualData, sankeyData] =
      await Promise.all([
        api('renewable_growth'),
        api('intensity_vs_gdp'),
        api('heatmap'),
        api('energy_mix?min_year=1900&max_year=2024'),
        api('annual_stats'),
        api('sankey'),
      ]);

    _growthData    = growthData;
    _intensityData = intensityData;
    _heatmapData   = heatmapData;
    _mixData       = mixAll;
    _annualData    = annualData;

    const f = getD2Filters();

    renderRenewableGrowth(growthData, f.src);
    renderIntensityGdp(intensityData, f.metric, f.decade);
    renderHeatmap(heatmapData);
    renderYoyChange(mixAll, f.decade);
    renderSankey(sankeyData);

    /* Table */
    _tblData = annualData;
    renderTable(f.decade, '');

    /* Wire controls */
    ['sourceSelect','decadeSelect','metricSelect'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('change', onD2Change);
    });

    const ts = document.getElementById('tableSearch');
    const td = document.getElementById('tableDecadeSelect');
    if (ts) ts.addEventListener('input', onD2Change);
    if (td) td.addEventListener('change', onD2Change);

    /* Sort headers */
    document.querySelectorAll('.data-tbl th[data-col]').forEach(th => {
      th.addEventListener('click', () => {
        const col = th.dataset.col;
        if (_sortCol === col) _sortAsc = !_sortAsc;
        else { _sortCol = col; _sortAsc = col === 'year'; }
        const f = getD2Filters();
        renderTable(f.decade, f.search);
      });
    });

  } catch (e) { console.error('[D2 error]', e); }
}

function getD2Filters() {
  const g = id => (document.getElementById(id) || {}).value || 'all';
  return {
    src:    g('sourceSelect'),
    decade: g('decadeSelect'),
    metric: g('metricSelect') || 'intensity',
    decade2:g('tableDecadeSelect'),
    search: (document.getElementById('tableSearch') || {}).value || '',
  };
}

function onD2Change() {
  if (!_growthData) return;
  const f = getD2Filters();
  renderRenewableGrowth(_growthData, f.src);
  renderIntensityGdp({ datapoints: [...(_intensityData?.datapoints || [])] }, f.metric, f.decade);
  renderHeatmap(_heatmapData);
  renderYoyChange(_mixData || [], f.decade);
  _tblPage = 1;
  renderTable(f.decade2, f.search);
}

/* ─── Entry ──────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  if (window.location.pathname.includes('analytical')) initDashboard2();
  else initDashboard1();
});
