/* ==============================================================
   Client-Side JavaScript — Rebuilt Capstone 3
   ============================================================== */

const state = {
    countries: [],
    indicators: [],
    map: null,
    charts: {},
    currentWave: 2019,
    currentSex: 'T'
};

// --- UTILITIES ---

async function fetchJSON(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
}

function getColor(value, quantiles) {
    if (value === null || value === undefined) return '#e2e8f0';
    // Find which quantile bucket the value falls into
    for (let i = 0; i < quantiles.length; i++) {
        if (value <= quantiles[i]) return ['#ebf8ff', '#bee3f8', '#90cdf4', '#63b3ed', '#4299e1'][i];
    }
    return '#2b6cb0';
}

// --- INITIALIZATION ---

async function initApp() {
    try {
        [state.countries, state.indicators] = await Promise.all([
            fetchJSON('/api/countries'),
            fetchJSON('/api/indicators')
        ]);

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

// --- DASHBOARD 1 (STRATEGIC) ---

async function initDashboard1() {
    populateDashboard1Filters();
    setupDashboard1Listeners();
    await refreshDashboard1();
}

function populateDashboard1Filters() {
    const paSelect = document.getElementById('pa-indicator');
    const cdSelect = document.getElementById('cd-indicator');
    const countrySelect = document.getElementById('country-select');
    const sexSelect = document.getElementById('sex-select');

    const paItems = state.indicators.filter(i => i.category_name === 'Physical Activity');
    const cdItems = state.indicators.filter(i => i.category_name === 'Chronic Disease');

    paSelect.innerHTML = paItems.map(i => `<option value="${i.indicator_code}">${i.indicator_label}</option>`).join('');
    cdSelect.innerHTML = cdItems.map(i => `<option value="${i.indicator_code}">${i.indicator_label}</option>`).join('');
    
    countrySelect.innerHTML = '<option value="">All Countries</option>' + 
        state.countries.filter(c => !c.country_code.startsWith('EU'))
            .map(c => `<option value="${c.country_code}">${c.country_name}</option>`).join('');

    sexSelect.innerHTML = '<option value="T">Total</option><option value="M">Male</option><option value="F">Female</option>';
}

function setupDashboard1Listeners() {
    ['wave-select', 'pa-indicator', 'cd-indicator', 'sex-select', 'country-select'].forEach(id => {
        document.getElementById(id).addEventListener('change', refreshDashboard1);
    });
}

async function refreshDashboard1() {
    const wave = document.getElementById('wave-select').value;
    const paInd = document.getElementById('pa-indicator').value;
    const cdInd = document.getElementById('cd-indicator').value;
    const sex = document.getElementById('sex-select').value;
    const country = document.getElementById('country-select').value;

    try {
        await Promise.all([
            loadKPIs(wave),
            loadMap(paInd, wave, sex),
            loadTopCountries(paInd, wave),
            loadTrend(paInd, sex),
            loadClassificationTable(wave, country, paInd, cdInd),
            loadInsights(paInd, wave)
        ]);
    } catch (err) {
        console.error('Refresh failed:', err);
    }
}

async function loadKPIs(wave) {
    const data = await fetchJSON(`/api/kpi?wave=${wave}`);
    document.getElementById('kpi-inactivity').textContent = data.avg_inactivity ? `${data.avg_inactivity}%` : 'N/A';
    document.getElementById('kpi-chronic').textContent = data.avg_chronic_prevalence ? `${data.avg_chronic_prevalence}%` : 'N/A';
    document.getElementById('kpi-high-burden').textContent = data.high_burden_countries || '0';
    document.getElementById('kpi-improved').textContent = data.most_improved_country || 'N/A';
    document.getElementById('kpi-improved-label').textContent = data.improvement ? `${data.improvement} pp improvement` : '';
}

async function loadMap(indicator, wave, sex) {
    const data = await fetchJSON(`/api/map-data?indicator=${indicator}&wave=${wave}&sex=${sex}`);
    if (state.map) state.map.remove();

    state.map = L.map('map').setView([50, 10], 3);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png').addTo(state.map);

    // Calculate quantiles for coloring
    const values = data.map(d => d.value).sort((a, b) => a - b);
    const quantiles = [
        values[Math.floor(values.length * 0.2)],
        values[Math.floor(values.length * 0.4)],
        values[Math.floor(values.length * 0.6)],
        values[Math.floor(values.length * 0.8)]
    ];

    fetch('https://raw.githubusercontent.com/leakyMirror/map-of-europe/master/GeoJSON/europe.geojson')
        .then(res => res.json())
        .then(geoData => {
            const layer = L.geoJSON(geoData, {
                style: (feature) => {
                    const country = data.find(d => d.country_code === (feature.properties.ISO2 || feature.properties.iso2));
                    return {
                        fillColor: country ? getColor(country.value, quantiles) : '#e2e8f0',
                        weight: 1, opacity: 1, color: 'white', fillOpacity: 0.8
                    };
                },
                onEachFeature: (feature, layer) => {
                    const country = data.find(d => d.country_code === (feature.properties.ISO2 || feature.properties.iso2));
                    if (country) {
                        layer.bindTooltip(`<strong>${country.country_name}</strong><br>${country.value}%`);
                    }
                }
            }).addTo(state.map);
            state.map.fitBounds(layer.getBounds());
        });
}

async function loadTopCountries(indicator, wave) {
    const data = await fetchJSON(`/api/top-countries?indicator=${indicator}&wave=${wave}&n=10`);
    const ctx = document.getElementById('top-countries-chart').getContext('2d');
    if (state.charts.top) state.charts.top.destroy();
    
    state.charts.top = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.combined_score ? d.country_name : d.country_name).reverse(), // Adjusting based on API output
            datasets: [{
                label: 'Score',
                data: data.map(d => d.combined_score || d.value || 0).reverse(),
                backgroundColor: '#3b82f6'
            }]
        },
        options: { indexAxis: 'y', responsive: true, plugins: { legend: { display: false } } }
    });
}

async function loadTrend(indicator, sex) {
    const data = await fetchJSON(`/api/trend?indicator=${indicator}&sex=${sex}`);
    const ctx = document.getElementById('trend-chart').getContext('2d');
    if (state.charts.trend) state.charts.trend.destroy();

    state.charts.trend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.year),
            datasets: [{
                label: 'EU Average (%)',
                data: data.map(d => d.avg_value),
                borderColor: '#3b82f6',
                tension: 0.3,
                fill: true,
                backgroundColor: 'rgba(59, 130, 246, 0.1)'
            }]
        },
        options: { responsive: true }
    });
}

async function loadClassificationTable(wave, countryCode, paInd, cdInd) {
    const inactivity = await fetchJSON(`/api/map-data?indicator=${paInd}&wave=${wave}&sex=T`);
    const chronic = await fetchJSON(`/api/map-data?indicator=${cdInd}&wave=${wave}&sex=T`);
    const tbody = document.getElementById('table-body');
    tbody.innerHTML = '';

    const combined = inactivity.map(act => {
        const c = chronic.find(item => item.country_code === act.country_code);
        return {
            name: act.country_name,
            code: act.country_code,
            inactivity: act.value,
            chronic: c ? c.value : null
        };
    }).filter(item => !countryCode || item.code === countryCode)
      .sort((a, b) => b.inactivity - a.inactivity);

    combined.forEach(row => {
        const isHigh = row.inactivity > 45 && row.chronic > 30;
        const tr = document.createElement('tr');
        if (isHigh) tr.classList.add('risk-band');
        tr.innerHTML = `
            <td>${row.name}</td>
            <td>${row.inactivity}%</td>
            <td>${row.chronic ? row.chronic + '%' : 'N/A'}</td>
            <td>${isHigh ? '<span class="risk-badge">High Burden</span>' : '—'}</td>
        `;
        tbody.appendChild(tr);
    });
}

async function loadInsights(indicator, wave) {
    const list = document.getElementById('insights-list');
    try {
        const data = await fetchJSON(`/api/insights?indicator=${indicator}&wave=${wave}`);
        if (data.length === 0) {
            list.innerHTML = '<li>No significant insights for this selection.</li>';
            return;
        }
        list.innerHTML = data.map(i => `
            <li>
                <strong>${i.country_info}</strong>: Concerning level detected for <em>${i.indicator_label}</em> 
                with an average value of <strong>${i.average_value}%</strong>.
                <div style="font-size: 0.7rem; color: gray;">Reported: ${i.report_date}</div>
            </li>
        `).join('');
    } catch (e) {
        list.innerHTML = '<li>Error loading insights.</li>';
    }
}

// --- DASHBOARD 2 (ANALYTICAL) ---

async function initDashboard2() {
    populateDashboard2Filters();
    setupDashboard2Listeners();
    await refreshDashboard2();
}

function populateDashboard2Filters() {
    const paSelect = document.getElementById('pa-indicator-d2');
    const condSelect = document.getElementById('condition-select');
    const countrySelect = document.getElementById('country-select');
    const sexSelect = document.getElementById('sex-select');

    const paItems = state.indicators.filter(i => i.category_name === 'Physical Activity');
    const cdItems = state.indicators.filter(i => i.category_name === 'Chronic Disease');

    paSelect.innerHTML = paItems.map(i => `<option value="${i.indicator_code}">${i.indicator_label}</option>`).join('');
    condSelect.innerHTML = cdItems.map(i => `<option value="${i.indicator_code}">${i.indicator_label}</option>`).join('');
    
    // Multi-select implementation (using a standard select with multiple attribute or a custom one)
    // Since standard select multiple is hard to style, I'll use it and note it.
    // But requirements say "Country multi-select". I'll use <select multiple>
    countrySelect.innerHTML = state.countries.filter(c => !c.country_code.startsWith('EU'))
        .map(c => `<option value="${c.country_code}">${c.country_name}</option>`).join('');

    sexSelect.innerHTML = '<option value="T">Total</option><option value="M">Male</option><option value="F">Female</option>';
}

function setupDashboard2Listeners() {
    ['wave-select', 'wave-select-b', 'pa-indicator-d2', 'condition-select', 'sex-select', 'country-select'].forEach(id => {
        document.getElementById(id).addEventListener('change', refreshDashboard2);
    });
    document.querySelectorAll('.age-cb').forEach(cb => {
        cb.addEventListener('change', refreshDashboard2);
    });
}

async function refreshDashboard2() {
    const waveA = document.getElementById('wave-select').value;
    const waveB = document.getElementById('wave-select-b').value;
    const paInd = document.getElementById('pa-indicator-d2').value;
    const cond = document.getElementById('condition-select').value;
    const sex = document.getElementById('sex-select').value;
    const selectedCountries = Array.from(document.getElementById('country-select').selectedOptions).map(o => o.value);
    const selectedAges = Array.from(document.querySelectorAll('.age-cb:checked')).map(cb => cb.value);

    try {
        await Promise.all([
            loadScatter(paInd, cond, waveA, waveB, sex),
            loadAgeBreakdown(selectedCountries, paInd, waveA, selectedAges),
            loadHeatmap(waveA),
            loadHistogram(cond, waveA),
            loadStackedArea(cond)
        ]);
    } catch (err) {
        console.error('Refresh failed:', err);
    }
}

async function loadScatter(pa, cond, wA, wB, sex) {
    const dataA = await fetchJSON(`/api/scatter?activity=${pa}&condition=${cond}&wave_a=${wA}&sex=${sex}`);
    let dataB = [];
    if (wB && wB !== wA) {
        dataB = await fetchJSON(`/api/scatter?activity=${pa}&condition=${cond}&wave_a=${wB}&sex=${sex}`);
    }

    const ctx = document.getElementById('scatter-chart').getContext('2d');
    if (state.charts.scatter) state.charts.scatter.destroy();

    const datasets = [{
        label: `Wave ${wA}`,
        data: dataA.map(d => ({ x: d.x, y: d.y, country: d.country })),
        backgroundColor: '#3b82f6'
    }];

    if (dataB.length > 0) {
        datasets.push({
            label: `Wave ${wB}`,
            data: dataB.map(d => ({ x: d.x, y: d.y, country: d.country })),
            backgroundColor: '#f59e0b',
            pointStyle: 'triangle'
        });
    }

    state.charts.scatter = new Chart(ctx, {
        type: 'scatter',
        data: { datasets },
        options: {
            scales: {
                x: { title: { display: true, text: 'Physical Inactivity (%)' } },
                y: { title: { display: true, text: 'Chronic Prevalence (%)' } }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.raw.country}: (${ctx.raw.x}%, ${ctx.raw.y}%)`
                    }
                }
            }
        }
    });
}

async function loadAgeBreakdown(countries, indicator, wave, ages) {
    // Note: The API only handles one country at a time for age breakdown.
    // For multi-select, we'd need a better API or fetch sequentially.
    // I'll fetch for the FIRST selected country to keep it simple and performant, 
    // or implement multiple fetches if required.
    // Let's implement multiple fetches for all selected countries.
    
    let allData = [];
    const promises = countries.map(c => 
        fetchJSON(`/api/age-breakdown?country=${c}&indicator=${indicator}&wave=${wave}`)
            .then(data => data.map(d => ({ ...d, country_code: c })))
            .catch(() => [])
    );
    
    const results = await Promise.all(promises);
    allData = results.flat();

    const filtered = allData.filter(d => ages.includes(d.age_code));

    const ctx = document.getElementById('age-breakdown-chart').getContext('2d');
    if (state.charts.age) state.charts.age.destroy();

    // Group by age and sex for the chart
    const ageGroups = [...new Set(filtered.map(d => d.age_group))];
    const sexes = ['Female', 'Male', 'Total'];
    
    state.charts.age = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ageGroups,
            datasets: sexes.map(s => ({
                label: s,
                data: ageGroups.map(ag => {
                    const match = filtered.find(f => f.age_group === ag && f.sex === s);
                    return match ? match.value : 0;
                }),
                backgroundColor: s === 'Female' ? '#ef4444' : s === 'Male' ? '#3b82f6' : '#64748b'
            }))
        },
        options: { responsive: true }
    });
}

async function loadHeatmap(wave) {
    const data = await fetchJSON(`/api/heatmap?wave=${wave}`);
    const tbody = document.getElementById('heatmap-body');
    const thead = document.getElementById('heatmap-head');
    
    const conditions = [...new Set(data.map(d => d.indicator_label))];
    const countries = [...new Set(data.map(d => d.country_name))];

    thead.innerHTML = `<tr><th>Country</th>${conditions.map(c => `<th>${c}</th>`).join('')}</tr>`;
    tbody.innerHTML = countries.map(c => {
        const cells = conditions.map(cond => {
            const d = data.find(item => item.country_name === c && item.indicator_label === cond);
            const val = d ? d.value : null;
            const color = val !== null ? `rgba(59, 130, 246, ${val/100})` : 'transparent';
            return `<td style="background-color: ${color}">${val !== null ? val + '%' : '--'}</td>`;
        }).join('');
        return `<tr><td><strong>${c}</strong></td>${cells}</tr>`;
    }).join('');
}

async function loadHistogram(indicator, wave) {
    const data = await fetchJSON(`/api/histogram?indicator=${indicator}&wave=${wave}`);
    const ctx = document.getElementById('histogram-chart').getContext('2d');
    if (state.charts.hist) state.charts.hist.destroy();

    state.charts.hist = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.value_bucket + '%'),
            datasets: [{
                label: 'Frequency',
                data: data.map(d => d.frequency),
                backgroundColor: '#3b82f6'
            }]
        },
        options: { responsive: true }
    });
}

async function loadStackedArea(indicator) {
    const [total, male, female] = await Promise.all([
        fetchJSON(`/api/trend?indicator=${indicator}&sex=T`),
        fetchJSON(`/api/trend?indicator=${indicator}&sex=M`),
        fetchJSON(`/api/trend?indicator=${indicator}&sex=F`)
    ]);

    const ctx = document.getElementById('stacked-area-chart').getContext('2d');
    if (state.charts.area) state.charts.area.destroy();

    const years = total.map(d => d.year);
    state.charts.area = new Chart(ctx, {
        type: 'line',
        data: {
            labels: years,
            datasets: [
                { label: 'Female', data: years.map(y => female.find(d => d.year === y)?.avg_value || 0), borderColor: '#ef4444', fill: false },
                { label: 'Male', data: years.map(y => male.find(d => d.year === y)?.avg_value || 0), borderColor: '#3b82f6', fill: false },
                { label: 'Total', data: total.map(d => d.avg_value), borderColor: '#10b981', borderDash: [5, 5], fill: false }
            ]
        },
        options: { responsive: true }
    });
}

document.addEventListener('DOMContentLoaded', initApp);
