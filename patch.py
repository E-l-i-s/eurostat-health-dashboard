
import sys

path = 'c:/Users/elisa/Desktop/KEMV-Final/Capstone3/static/script.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_str = '''async function refreshDashboard1() {
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
}'''

new_str = '''async function refreshDashboard1() {
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
            loadClassificationTable(wave, countryCode),
            loadInsights(condition, wave)
        ]);
    } catch (err) {
        console.error('Dashboard refresh failed:', err);
    }
}

async function loadInsights(indicator, wave) {
    try {
        const insightsList = document.getElementById('insights-list');
        if (!insightsList) return;
        const response = await fetch('/api/insights?indicator=' + indicator + '&wave=' + wave);
        if (!response.ok) {
            insightsList.innerHTML = '<li>No advanced insights available for these parameters.</li>';
            return;
        }
        const data = await response.json();
        if (data.length === 0) {
            insightsList.innerHTML = '<li>No advanced insights available.</li>';
            return;
        }
        insightsList.innerHTML = '';
        data.forEach(item => {
            const li = document.createElement('li');
            li.style.marginBottom = '8px';
            li.innerHTML = '<strong>' + item.country_info + '</strong>: High burden detected for <em>' + item.indicator_label + '</em> with an average value of <strong>' + item.average_value + '%</strong>. <span style=\'color: #6B7280; font-size: 12px;\\'>(Generated: ' + item.report_date + ')</span>';
            insightsList.appendChild(li);
        });
    } catch (err) {
        console.error('Insights load failed:', err);
    }
}'''

if old_str in content:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.replace(old_str, new_str))
    print('Patched successfully')
else:
    print('old_str not found')

