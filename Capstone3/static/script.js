/* ==============================================================
   Client-Side JavaScript — Both Dashboards
   Physical Activity & Chronic Disease Burden Across Europe
   ============================================================== */

// ==============================================================
// STATE
// ==============================================================
const state = {
    countries: [],
    indicators: [],
    waves: [],
    map: null,
    mapData: null,
    charts: {}
};

const COLOR_SCALE = ['#DBEAFE', '#93C5FD', '#5B8ED6', '#2E5F9E', '#1E3A5F'];

// ==============================================================
// UTILITY FUNCTIONS
// ==============================================================
function getColor(value, min, max) {
    if (value === null || value === undefined) return '#DDD';
    const normalized = (value - min) / (max - min);
    const index = Math.min(Math.floor(normalized * COLOR_SCALE.length), COLOR_SCALE.length - 1);
    return COLOR_SCALE[Math.max(0, index)];
}

function isHighBurden(inactivity, chronic) {
    return inactivity > 45 && chronic > 30;
}

async function fetchJSON(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
}

// ==============================================================
// INITIALIZATION
// ==============================================================
async function initApp() {
    try {
        state.countries = await fetchJSON('/api/countries');
        state.indicators = await fetchJSON('/api/indicators');
        state.waves = await fetchJSON('/api/waves');
        populateFilters();
        const isDashboard2 = window.location.pathname.includes('analytics');
        if (isDashboard2) {
            await initDashboard2();
        } else {
            await initDashboard1();
        }
    } catch (err) {
        console.error('Initialization failed:', err);
    }
}

function populateFilters() {
    const conditionSelects = document.querySelectorAll('#condition-select');
    conditionSelects.forEach(select => {
        if (!select) return;
        select.innerHTML = '';
        const activityItems = state.indicators.filter(i => i.category_name === 'Physical Activity');
        const chronicItems = state.indicators.filter(i => i.category_name === 'Chronic Disease');
        const allItems = [...activityItems, ...chronicItems];
        allItems.forEach(ind => {
            const opt = document.createElement('option');
            opt.value = ind.indicator_code;
            opt.textContent = ind.indicator_label;
            select.appendChild(opt);
        });
    });

    const countryMulti = document.getElementById('country-multi');
    if (countryMulti) {
        countryMulti.innerHTML = '';
        state.countries.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.country_code;
            opt.textContent = c.country_name;
            countryMulti.appendChild(opt);
        });
    }

    const countrySelect = document.getElementById('country-select');
    if (countrySelect) {
        countrySelect.innerHTML = '<option value="">All Countries</option>';
        state.countries.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.country_code;
            opt.textContent = c.country_name;
            countrySelect.appendChild(opt);
        });
    }
}

// ==============================================================
// DASHBOARD 1 — STRATEGIC
// ==============================================================
async function initDashboard1() {
    setupFilterListeners1();
    await refreshDashboard1();
}

async function refreshDashboard1() {
    const wave = document.getElementById('wave-select').value;
    const condition = document.getElementById('condition-select').value;
    const sex = document.getElementById('sex-select').value;
    const countryCode = document.getElementById('country-select')?.value || '';
    try {
        await Promise.all([
            loadKPI(wave),
            loadMapData(condition, wave, sex),
            loadTopCountries(condition, wave),
            loadTrend(condition, sex),
            loadClassificationTable(wave, countryCode)
        ]);
    } catch (err) {
        console.error('Dashboard refresh failed:', err);
    }
}

function setupFilterListeners1() {
    document.getElementById('wave-select').addEventListener('change', refreshDashboard1);
    document.getElementById('condition-select').addEventListener('change', refreshDashboard1);
    document.getElementById('sex-select').addEventListener('change', refreshDashboard1);
    const countrySelect = document.getElementById('country-select');
    if (countrySelect) countrySelect.addEventListener('change', refreshDashboard1);
}

// --- KPI ---
async function loadKPI(wave) {
    try {
        const data = await fetchJSON(`/api/kpi?wave=${wave}`);
        document.getElementById('kpi-inactivity').textContent =
            data.avg_inactivity !== null ? data.avg_inactivity + '%' : 'N/A';
        document.getElementById('kpi-chronic').textContent =
            data.avg_chronic_prevalence !== null ? data.avg_chronic_prevalence + '%' : 'N/A';
        document.getElementById('kpi-high-burden').textContent =
            data.high_burden_countries !== null ? data.high_burden_countries : 'N/A';
        if (data.most_improved_country) {
            document.getElementById('kpi-improved').textContent = data.most_improved_country;
            document.getElementById('kpi-improved-label').textContent =
                data.improvement ? `${data.improvement} pp improvement` : 'most improved';
        } else {
            document.getElementById('kpi-improved').textContent = 'N/A';
        }
    } catch (err) {
        console.error('KPI load failed:', err);
    }
}

// --- MAP ---
async function loadMapData(indicator, wave, sex) {
    try {
        const data = await fetchJSON(`/api/map-data?indicator=${indicator}&wave=${wave}&sex=${sex}`);
        state.mapData = data;
        renderMap(data);
    } catch (err) {
        console.error('Map data load failed:', err);
    }
}

function renderMap(data) {
    if (state.map) {
        state.map.remove();
        state.map = null;
    }
    state.map = L.map('map').setView([50, 10], 3);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
        maxZoom: 18
    }).addTo(state.map);

    const values = data.map(d => d.value).filter(v => v !== null);
    const min = Math.min(...values);
    const max = Math.max(...values);

    fetch('https://raw.githubusercontent.com/leakyMirror/map-of-europe/master/GeoJSON/europe.geojson')
        .then(res => res.json())
        .then(geoData => {
            const geoLayer = L.geoJSON(geoData, {
                style: feature => {
                    const countryData = data.find(
                        d => d.country_code === feature.properties.ISO2 || d.country_code === feature.properties.iso2
                    );
                    const value = countryData ? countryData.value : null;
                    const inactivity = value || 0;
                    const chronicData = state.mapData ? state.mapData.find(
                        d => d.country_code === (feature.properties.ISO2 || feature.properties.iso2)
                    ) : null;
                    const chronic = chronicData ? chronicData.value : 0;
                    const isHigh = isHighBurden(inactivity, chronic);
                    return {
                        fillColor: getColor(value, min, max),
                        weight: isHigh ? 2 : 1,
                        opacity: 1,
                        color: isHigh ? '#C0392B' : '#E5E7EB',
                        fillOpacity: 0.8
                    };
                },
                onEachFeature: (feature, layer) => {
                    const countryData = data.find(
                        d => d.country_code === feature.properties.ISO2 || d.country_code === feature.properties.iso2
                    );
                    const countryName = countryData ? countryData.country_name : feature.properties.NAME || 'Unknown';
                    const value = countryData ? countryData.value : 'No data';
                    const tooltipContent = `<strong>${countryName}</strong><br>Value: ${value}%`;
                    layer.bindTooltip(tooltipContent, { sticky: true });
                    layer.on('mouseout', () => {
                        if (layer.getTooltip()) layer.closeTooltip();
                    });
                }
            }).addTo(state.map);
            state.map.fitBounds(geoLayer.getBounds().pad(0.1));
        })
        .catch(err => {
            console.error('GeoJSON load failed:', err);
            Object.keys(countryCentroids).forEach(code => {
                const countryData = data.find(d => d.country_code === code);
                if (countryData && countryCentroids[code]) {
                    const c = countryCentroids[code];
                    const isHigh = isHighBurden(countryData.value, 0);
                    const circle = L.circleMarker([c.lat, c.lng], {
                        radius: 8,
                        fillColor: getColor(countryData.value, min, max),
                        color: isHigh ? '#C0392B' : '#E5E7EB',
                        weight: isHigh ? 2 : 1,
                        fillOpacity: 0.8
                    }).addTo(state.map);
                    circle.bindTooltip(`<strong>${countryData.country_name}</strong><br>Value: ${countryData.value}%`);
                }
            });
            state.map.setView([50, 10], 3);
        });
}

const countryCentroids = {
    'AT': { lat: 47.5, lng: 14.5 }, 'BE': { lat: 50.5, lng: 4.5 },
    'BG': { lat: 42.7, lng: 25.5 }, 'HR': { lat: 45.1, lng: 15.5 },
    'CY': { lat: 35.0, lng: 33.0 }, 'CZ': { lat: 49.8, lng: 15.5 },
    'DK': { lat: 56.0, lng: 10.0 }, 'EE': { lat: 58.6, lng: 25.0 },
    'FI': { lat: 64.0, lng: 26.0 }, 'FR': { lat: 46.5, lng: 2.5 },
    'DE': { lat: 51.0, lng: 10.0 }, 'GR': { lat: 39.0, lng: 22.0 },
    'HU': { lat: 47.0, lng: 19.0 }, 'IE': { lat: 53.0, lng: -8.0 },
    'IT': { lat: 41.9, lng: 12.5 }, 'LV': { lat: 57.0, lng: 25.0 },
    'LT': { lat: 55.0, lng: 24.0 }, 'LU': { lat: 49.8, lng: 6.1 },
    'MT': { lat: 35.9, lng: 14.4 }, 'NL': { lat: 52.0, lng: 5.0 },
    'PL': { lat: 52.0, lng: 19.0 }, 'PT': { lat: 39.5, lng: -8.0 },
    'RO': { lat: 46.0, lng: 25.0 }, 'SK': { lat: 48.7, lng: 19.5 },
    'SI': { lat: 46.1, lng: 14.5 }, 'ES': { lat: 40.0, lng: -3.0 },
    'SE': { lat: 62.0, lng: 15.0 }, 'NO': { lat: 62.0, lng: 10.0 },
    'CH': { lat: 46.8, lng: 8.0 }, 'IS': { lat: 65.0, lng: -18.0 },
    'LI': { lat: 47.1, lng: 9.5 }, 'MT': { lat: 35.9, lng: 14.4 },
    'ME': { lat: 42.7, lng: 19.0 }, 'MK': { lat: 41.6, lng: 21.7 },
    'AL': { lat: 41.0, lng: 20.0 }, 'RS': { lat: 44.0, lng: 21.0 },
    'TR': { lat: 39.0, lng: 35.0 }, 'BA': { lat: 44.0, lng: 18.0 }
};

// --- TOP COUNTRIES BAR CHART ---
async function loadTopCountries(indicator, wave) {
    try {
        const data = await fetchJSON(`/api/top-countries?indicator=${indicator}&wave=${wave}&n=10`);
        renderTopCountriesChart(data);
    } catch (err) {
        console.error('Top countries load failed:', err);
    }
}

function renderTopCountriesChart(data) {
    if (state.charts.topCountries) {
        state.charts.topCountries.destroy();
    }
    const ctx = document.getElementById('top-countries-chart');
    if (!ctx) return;
    const labels = data.map(d => d.country_name).reverse();
    const values = data.map(d => d.value).reverse();
    state.charts.topCountries = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Inactivity Rate (%)',
                data: values,
                backgroundColor: labels.map((_, i) => {
                    const v = values[i];
                    return v > 55 ? '#C0392B' : v > 45 ? '#E67E22' : '#1D6FA4';
                }),
                borderRadius: 3
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#fff',
                    borderColor: '#E5E7EB',
                    borderWidth: 1,
                    titleFont: { family: 'Inter', size: 13 },
                    bodyFont: { family: 'Inter', size: 13 },
                    padding: 10,
                    cornerRadius: 6
                }
            },
            scales: {
                x: {
                    grid: { color: '#E5E7EB' },
                    ticks: { font: { family: 'Inter', size: 12 }, color: '#6B7280' }
                },
                y: {
                    grid: { display: false },
                    ticks: { font: { family: 'Inter', size: 12 }, color: '#6B7280' }
                }
            }
        }
    });
}

// --- TREND LINE ---
async function loadTrend(indicator, sex) {
    try {
        const data = await fetchJSON(`/api/trend?indicator=${indicator}&sex=${sex}`);
        renderTrendChart(data);
    } catch (err) {
        console.error('Trend load failed:', err);
    }
}

function renderTrendChart(data) {
    if (state.charts.trend) {
        state.charts.trend.destroy();
    }
    const ctx = document.getElementById('trend-chart');
    if (!ctx) return;
    state.charts.trend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.year),
            datasets: [{
                label: 'EU Average (%)',
                data: data.map(d => d.avg_value),
                borderColor: '#1D6FA4',
                backgroundColor: 'rgba(29, 111, 164, 0.1)',
                fill: true,
                tension: 0.3,
                pointBackgroundColor: '#1D6FA4',
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#fff',
                    borderColor: '#E5E7EB',
                    borderWidth: 1,
                    titleFont: { family: 'Inter', size: 13 },
                    bodyFont: { family: 'Inter', size: 13 },
                    padding: 10,
                    cornerRadius: 6
                }
            },
            scales: {
                x: {
                    grid: { color: '#E5E7EB' },
                    ticks: { font: { family: 'Inter', size: 12 }, color: '#6B7280' }
                },
                y: {
                    grid: { color: '#E5E7EB' },
                    ticks: { font: { family: 'Inter', size: 12 }, color: '#6B7280' },
                    beginAtZero: false
                }
            }
        }
    });
}

// --- CLASSIFICATION TABLE ---
async function loadClassificationTable(wave, countryCode) {
    try {
        const inactivityData = await fetchJSON(`/api/map-data?indicator=${getActivityIndicator()}&wave=${wave}&sex=T`);
        const chronicData = await fetchJSON(`/api/map-data?indicator=${getChronicIndicator()}&wave=${wave}&sex=T`);
        const tableBody = document.getElementById('table-body');
        if (!tableBody) return;
        tableBody.innerHTML = '';
        const combined = inactivityData.map(act => {
            const chronic = chronicData.find(c => c.country_code === act.country_code);
            return {
                country_name: act.country_name,
                country_code: act.country_code,
                inactivity: act.value,
                chronic: chronic ? chronic.value : null
            };
        }).sort((a, b) => b.inactivity - a.inactivity);
        combined.forEach(row => {
            if (countryCode && row.country_code !== countryCode) return;
            const tr = document.createElement('tr');
            const isHigh = isHighBurden(row.inactivity, row.chronic);
            if (isHigh) {
                tr.classList.add('risk-band');
            }
            tr.innerHTML = `
                <td>${row.country_name}</td>
                <td>${row.inactivity !== null ? row.inactivity + '%' : 'N/A'}</td>
                <td>${row.chronic !== null ? row.chronic + '%' : 'N/A'}</td>
                <td>${isHigh ? '<span class="risk-badge">High Burden</span>' : '—'}</td>
            `;
            tableBody.appendChild(tr);
        });
        setupTableSearch(combined);
    } catch (err) {
        console.error('Classification table load failed:', err);
    }
}

function getActivityIndicator() {
    const select = document.getElementById('condition-select');
    if (!select) return 'MV_AERO_SPRT';
    return select.value || 'MV_AERO_SPRT';
}

function getChronicIndicator() {
    const chronicItems = state.indicators.filter(i => i.category_name === 'Chronic Disease');
    return chronicItems.length > 0 ? chronicItems[0].indicator_code : 'HBLPR';
}

function setupTableSearch(allData) {
    const searchInput = document.getElementById('country-search');
    if (!searchInput) return;
    searchInput.addEventListener('input', function() {
        const term = this.value.toLowerCase();
        const rows = document.querySelectorAll('#table-body tr');
        rows.forEach((row, index) => {
            if (index >= allData.length) return;
            const country = allData[index].country_name.toLowerCase();
            row.style.display = country.includes(term) ? '' : 'none';
        });
    });
}

// ==============================================================
// DASHBOARD 2 — ANALYTICAL
// ==============================================================
async function initDashboard2() {
    setupFilterListeners2();
    await refreshDashboard2();
}

async function refreshDashboard2() {
    const waveA = document.getElementById('wave-select').value;
    const waveB = document.getElementById('wave-select-b').value;
    const condition = document.getElementById('condition-select').value;
    const sex = document.getElementById('sex-select').value;
    const countryMulti = document.getElementById('country-multi');
    const selectedCountries = countryMulti ? Array.from(countryMulti.selectedOptions).map(o => o.value) : [];
    const countryCode = selectedCountries.length > 0 ? selectedCountries[0] : 'DE';
    try {
        await Promise.all([
            loadScatterPlot(condition, waveA, sex, waveB),
            loadAgeBreakdown(countryCode, condition, waveA),
            loadHeatmap(waveA),
            loadHistogram(condition, waveA),
            loadStackedArea(condition)
        ]);
    } catch (err) {
        console.error('Dashboard 2 refresh failed:', err);
    }
}

function setupFilterListeners2() {
    document.getElementById('wave-select').addEventListener('change', refreshDashboard2);
    document.getElementById('wave-select-b').addEventListener('change', refreshDashboard2);
    document.getElementById('condition-select').addEventListener('change', refreshDashboard2);
    document.getElementById('sex-select').addEventListener('change', refreshDashboard2);
    document.getElementById('country-multi').addEventListener('change', refreshDashboard2);
    document.querySelectorAll('.age-cb').forEach(cb => {
        cb.addEventListener('change', refreshDashboard2);
    });
}

// --- SCATTER PLOT ---
async function loadScatterPlot(condition, waveA, sex, waveB) {
    const activityCode = getActivityIndicator();
    try {
        const [dataA, dataB] = await Promise.all([
            fetchJSON(`/api/scatter?activity=${activityCode}&condition=${condition}&wave=${waveA}&sex=${sex}`),
            waveB && waveB !== waveA
                ? fetchJSON(`/api/scatter?activity=${activityCode}&condition=${condition}&wave=${waveB}&sex=${sex}`)
                : Promise.resolve([])
        ]);
        renderScatterPlot(dataA, dataB, waveA, waveB);
    } catch (err) {
        console.error('Scatter load failed:', err);
    }
}

function renderScatterPlot(dataA, dataB, waveALabel, waveBLabel) {
    if (state.charts.scatter) {
        state.charts.scatter.destroy();
    }
    const ctx = document.getElementById('scatter-chart');
    if (!ctx) return;
    const datasets = [
        {
            label: waveALabel || 'Wave A',
            data: dataA.map(d => ({
                x: d.inactivity_rate,
                y: d.chronic_prevalence,
                country: d.country_name
            })),
            backgroundColor: dataA.map(d => {
                return isHighBurden(d.inactivity_rate, d.chronic_prevalence)
                    ? '#C0392B' : '#1D6FA4';
            }),
            pointRadius: 6,
            pointHoverRadius: 8
        }
    ];
    if (dataB && dataB.length > 0) {
        datasets.push({
            label: waveBLabel || 'Wave B',
            data: dataB.map(d => ({
                x: d.inactivity_rate,
                y: d.chronic_prevalence,
                country: d.country_name
            })),
            backgroundColor: '#F59E0B',
            pointRadius: 5,
            pointHoverRadius: 7,
            pointStyle: 'triangle'
        });
    }
    state.charts.scatter = new Chart(ctx, {
        type: 'scatter',
        data: { datasets },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { font: { family: 'Inter', size: 12 }, color: '#6B7280', usePointStyle: true }
                },
                tooltip: {
                    backgroundColor: '#fff',
                    borderColor: '#E5E7EB',
                    borderWidth: 1,
                    titleFont: { family: 'Inter', size: 13 },
                    bodyFont: { family: 'Inter', size: 13 },
                    padding: 10,
                    cornerRadius: 6,
                    callbacks: {
                        label: ctx2 => {
                            const d = ctx2.raw;
                            return `${d.country}: Inactivity ${d.x}%, Chronic ${d.y}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: '#E5E7EB' },
                    ticks: { font: { family: 'Inter', size: 12 }, color: '#6B7280' },
                    title: {
                        display: true,
                        text: 'Physical Inactivity Rate (%)',
                        font: { family: 'Inter', size: 13 },
                        color: '#6B7280'
                    }
                },
                y: {
                    grid: { color: '#E5E7EB' },
                    ticks: { font: { family: 'Inter', size: 12 }, color: '#6B7280' },
                    title: {
                        display: true,
                        text: 'Chronic Disease Prevalence (%)',
                        font: { family: 'Inter', size: 13 },
                        color: '#6B7280'
                    }
                }
            }
        }
    });
}

// --- AGE BREAKDOWN ---
async function loadAgeBreakdown(country, indicator, wave) {
    try {
        const data = await fetchJSON(`/api/age-breakdown?country=${country}&indicator=${indicator}&wave=${wave}`);
        const checkedAges = Array.from(document.querySelectorAll('.age-cb:checked')).map(cb => cb.value);
        const filtered = checkedAges.length > 0 ? data.filter(d => checkedAges.includes(d.age_code)) : data;
        renderAgeBreakdown(filtered.length > 0 ? filtered : data);
    } catch (err) {
        console.error('Age breakdown load failed:', err);
    }
}

function renderAgeBreakdown(data) {
    if (state.charts.ageBreakdown) {
        state.charts.ageBreakdown.destroy();
    }
    const ctx = document.getElementById('age-breakdown-chart');
    if (!ctx) return;
    const ageGroups = [...new Set(data.map(d => d.age_group))];
    const sexes = ['Female', 'Male', 'Total'];
    const datasets = sexes.map(sex => {
        return {
            label: sex,
            data: ageGroups.map(ag => {
                const match = data.find(d => d.age_group === ag && d.sex === sex);
                return match ? match.value : null;
            }),
            backgroundColor: sex === 'Female' ? '#C0392B' : sex === 'Male' ? '#1D6FA4' : '#6B7280'
        };
    });
    state.charts.ageBreakdown = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ageGroups,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { font: { family: 'Inter', size: 12 }, color: '#6B7280' }
                },
                tooltip: {
                    backgroundColor: '#fff',
                    borderColor: '#E5E7EB',
                    borderWidth: 1,
                    titleFont: { family: 'Inter', size: 13 },
                    bodyFont: { family: 'Inter', size: 13 },
                    padding: 10,
                    cornerRadius: 6
                }
            },
            scales: {
                x: {
                    grid: { color: '#E5E7EB' },
                    ticks: { font: { family: 'Inter', size: 11 }, color: '#6B7280', maxRotation: 45 }
                },
                y: {
                    grid: { color: '#E5E7EB' },
                    ticks: { font: { family: 'Inter', size: 12 }, color: '#6B7280' },
                    beginAtZero: true
                }
            }
        }
    });
}

// --- HEATMAP ---
async function loadHeatmap(wave) {
    try {
        const data = await fetchJSON(`/api/heatmap?wave=${wave}`);
        renderHeatmap(data);
    } catch (err) {
        console.error('Heatmap load failed:', err);
    }
}

function renderHeatmap(data) {
    const thead = document.getElementById('heatmap-head');
    const tbody = document.getElementById('heatmap-body');
    if (!thead || !tbody) return;
    const conditions = [...new Set(data.map(d => d.indicator_label))];
    const countries = [...new Set(data.map(d => d.country_name))];
    const values = data.map(d => d.value).filter(v => v !== null);
    const min = Math.min(...values);
    const max = Math.max(...values);

    thead.innerHTML = '<tr><th>Country</th>' + conditions.map(c => `<th>${c}</th>`).join('') + '</tr>';
    tbody.innerHTML = countries.map(country => {
        const cells = conditions.map(cond => {
            const match = data.find(d => d.country_name === country && d.indicator_label === cond);
            const value = match ? match.value : null;
            const color = value !== null ? getColor(value, min, max) : '#F8F9FB';
            return `<td style="background:${color}; color: ${value > (min + max) / 2 ? '#fff' : '#111827'}">${value !== null ? value + '%' : '—'}</td>`;
        }).join('');
        return `<tr><td><strong>${country}</strong></td>${cells}</tr>`;
    }).join('');
}

// --- HISTOGRAM ---
async function loadHistogram(indicator, wave) {
    try {
        const data = await fetchJSON(`/api/histogram?indicator=${indicator}&wave=${wave}`);
        renderHistogram(data);
    } catch (err) {
        console.error('Histogram load failed:', err);
    }
}

function renderHistogram(data) {
    if (state.charts.histogram) {
        state.charts.histogram.destroy();
    }
    const ctx = document.getElementById('histogram-chart');
    if (!ctx) return;
    state.charts.histogram = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.value_bucket + '%'),
            datasets: [{
                label: 'Countries',
                data: data.map(d => d.frequency),
                backgroundColor: '#1D6FA4',
                borderRadius: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#fff',
                    borderColor: '#E5E7EB',
                    borderWidth: 1,
                    titleFont: { family: 'Inter', size: 13 },
                    bodyFont: { family: 'Inter', size: 13 },
                    padding: 10,
                    cornerRadius: 6
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { family: 'Inter', size: 11 }, color: '#6B7280', maxRotation: 45 }
                },
                y: {
                    grid: { color: '#E5E7EB' },
                    ticks: { font: { family: 'Inter', size: 12 }, color: '#6B7280' },
                    beginAtZero: true
                }
            }
        }
    });
}

// --- STACKED AREA ---
async function loadStackedArea(indicator) {
    try {
        const [totalData, maleData, femaleData] = await Promise.all([
            fetchJSON(`/api/trend?indicator=${indicator}&sex=T`),
            fetchJSON(`/api/trend?indicator=${indicator}&sex=M`),
            fetchJSON(`/api/trend?indicator=${indicator}&sex=F`)
        ]);
        renderStackedArea(totalData, maleData, femaleData);
    } catch (err) {
        console.error('Stacked area load failed:', err);
    }
}

function renderStackedArea(totalData, maleData, femaleData) {
    if (state.charts.stackedArea) {
        state.charts.stackedArea.destroy();
    }
    const ctx = document.getElementById('stacked-area-chart');
    if (!ctx) return;
    const years = totalData.map(d => d.year);
    state.charts.stackedArea = new Chart(ctx, {
        type: 'line',
        data: {
            labels: years,
            datasets: [
                {
                    label: 'Male',
                    data: years.map(y => {
                        const m = maleData.find(d => d.year === y);
                        return m ? m.avg_value : null;
                    }),
                    borderColor: '#1D6FA4',
                    backgroundColor: 'rgba(29, 111, 164, 0.1)',
                    fill: true,
                    tension: 0.3
                },
                {
                    label: 'Female',
                    data: years.map(y => {
                        const f = femaleData.find(d => d.year === y);
                        return f ? f.avg_value : null;
                    }),
                    borderColor: '#C0392B',
                    backgroundColor: 'rgba(192, 57, 43, 0.1)',
                    fill: true,
                    tension: 0.3
                },
                {
                    label: 'Total',
                    data: years.map(y => {
                        const t = totalData.find(d => d.year === y);
                        return t ? t.avg_value : null;
                    }),
                    borderColor: '#2E7D5E',
                    backgroundColor: 'rgba(46, 125, 94, 0.1)',
                    fill: true,
                    tension: 0.3,
                    borderDash: [5, 5]
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { font: { family: 'Inter', size: 12 }, color: '#6B7280' }
                },
                tooltip: {
                    backgroundColor: '#fff',
                    borderColor: '#E5E7EB',
                    borderWidth: 1,
                    titleFont: { family: 'Inter', size: 13 },
                    bodyFont: { family: 'Inter', size: 13 },
                    padding: 10,
                    cornerRadius: 6
                }
            },
            scales: {
                x: {
                    grid: { color: '#E5E7EB' },
                    ticks: { font: { family: 'Inter', size: 12 }, color: '#6B7280' }
                },
                y: {
                    grid: { color: '#E5E7EB' },
                    ticks: { font: { family: 'Inter', size: 12 }, color: '#6B7280' },
                    beginAtZero: false
                }
            }
        }
    });
}

// ==============================================================
// START
// ==============================================================
document.addEventListener('DOMContentLoaded', initApp);
