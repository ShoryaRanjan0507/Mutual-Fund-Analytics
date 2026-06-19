/**
 * Bluestock Insight 360 — Dashboard JavaScript
 * Light theme default, dark mode toggle, all charts + navigation.
 */

// ============================================
// Global State
// ============================================
let DATA = null;
let charts = {};
let currentTheme = 'light';

// ============================================
// Theme Colors (updated per theme)
// ============================================
function getColors() {
    const isDark = currentTheme === 'dark';
    return {
        primary: isDark ? '#38bdf8' : '#2563eb',
        primaryAlpha: isDark ? 'rgba(56,189,248,0.2)' : 'rgba(37,99,235,0.15)',
        purple: isDark ? '#a78bfa' : '#7c3aed',
        red: isDark ? '#fb7185' : '#ef4444',
        yellow: isDark ? '#fbbf24' : '#f59e0b',
        green: isDark ? '#34d399' : '#10b981',
        pink: isDark ? '#f472b6' : '#ec4899',
        orange: isDark ? '#fb923c' : '#f97316',
        lavender: isDark ? '#818cf8' : '#8b5cf6',
        text: isDark ? '#e8edf5' : '#111827',
        textSecondary: isDark ? '#94a3b8' : '#6b7280',
        gridLine: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.06)',
        gridBorder: isDark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.08)',
        tooltipBg: isDark ? 'rgba(26,34,54,0.95)' : 'rgba(255,255,255,0.97)',
        tooltipBorder: isDark ? 'rgba(56,189,248,0.2)' : '#e5e7eb',
        tooltipText: isDark ? '#e8edf5' : '#111827',
        positive: isDark ? '#34d399' : '#059669',
        negative: isDark ? '#fb7185' : '#dc2626',
        cardBg: isDark ? '#1a2236' : '#ffffff',
        muted: isDark ? '#ffffff44' : '#00000033',
        palette: isDark
            ? ['#38bdf8','#a78bfa','#fb7185','#fbbf24','#34d399','#f472b6','#fb923c','#818cf8','#22d3ee','#e879f9','#84cc16','#f87171']
            : ['#2563eb','#7c3aed','#ef4444','#f59e0b','#10b981','#ec4899','#f97316','#8b5cf6','#06b6d4','#d946ef','#65a30d','#dc2626']
    };
}

// ============================================
// Chart.js Global Defaults
// ============================================
function applyChartDefaults() {
    const C = getColors();
    Chart.defaults.color = C.textSecondary;
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.pointStyle = 'circle';
    Chart.defaults.plugins.legend.labels.padding = 14;
    Chart.defaults.plugins.tooltip.backgroundColor = C.tooltipBg;
    Chart.defaults.plugins.tooltip.titleColor = C.tooltipText;
    Chart.defaults.plugins.tooltip.bodyColor = C.tooltipText;
    Chart.defaults.plugins.tooltip.borderColor = C.tooltipBorder;
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.titleFont = { weight: '600' };
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
    Chart.defaults.elements.point.radius = 2;
    Chart.defaults.elements.point.hoverRadius = 5;
    Chart.defaults.elements.line.tension = 0.35;
    Chart.defaults.elements.bar.borderRadius = 5;
    Chart.defaults.scale.grid = { color: C.gridLine };
    Chart.defaults.scale.border = { color: C.gridBorder };
}

// ============================================
// Helpers
// ============================================
function fmt(num, dec = 0) {
    if (num == null || isNaN(num)) return '—';
    return Number(num).toLocaleString('en-IN', { maximumFractionDigits: dec });
}

function fmtCr(num) {
    if (num == null || isNaN(num)) return '—';
    const n = Number(num);
    if (n >= 1e7) return '₹' + (n / 1e7).toFixed(1) + 'L Cr';
    if (n >= 1e5) return '₹' + (n / 1e5).toFixed(1) + 'L Cr';
    if (n >= 1e3) return '₹' + (n / 1e3).toFixed(0) + 'K Cr';
    return '₹' + fmt(n) + ' Cr';
}

function fmtMoney(num) {
    if (num == null || isNaN(num)) return '—';
    const n = Number(num);
    if (n >= 1e9) return '₹' + (n / 1e9).toFixed(2) + 'B';
    if (n >= 1e7) return '₹' + (n / 1e7).toFixed(1) + ' Cr';
    if (n >= 1e5) return '₹' + (n / 1e5).toFixed(1) + 'L';
    if (n >= 1e3) return '₹' + (n / 1e3).toFixed(0) + 'K';
    return '₹' + fmt(n);
}

function shortName(name, max = 25) {
    if (!name) return '';
    name = name.replace(/ - Regular| - Direct| - Growth| Plan/g, '').trim();
    return name.length > max ? name.substring(0, max) + '…' : name;
}

function gradient(ctx, c1, c2) {
    const g = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
    g.addColorStop(0, c1);
    g.addColorStop(1, c2);
    return g;
}

// ============================================
// Init
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    applyChartDefaults();
    loadData();
    setupNavigation();
    setupMobileMenu();
    setupThemeToggle();
});

// ============================================
// Theme Toggle
// ============================================
function setupThemeToggle() {
    const saved = localStorage.getItem('bluestock-theme');
    if (saved === 'dark') {
        setTheme('dark');
    }
    
    document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
    document.getElementById('theme-toggle-mobile').addEventListener('click', toggleTheme);
}

function toggleTheme() {
    setTheme(currentTheme === 'light' ? 'dark' : 'light');
}

function setTheme(theme) {
    currentTheme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('bluestock-theme', theme);

    // Update toggle label
    const labels = document.querySelectorAll('.toggle-label');
    labels.forEach(l => l.textContent = theme === 'light' ? 'Dark Mode' : 'Light Mode');

    // Re-render all charts with new colors
    applyChartDefaults();
    reRenderAllCharts();
}

function reRenderAllCharts() {
    // Destroy all existing charts
    Object.keys(charts).forEach(key => {
        charts[key].destroy();
        delete charts[key];
    });
    // Reset rendered state and re-render current page
    Object.keys(rendered).forEach(k => rendered[k] = false);
    const activePage = document.querySelector('.nav-item.active');
    if (activePage) renderPage(activePage.dataset.page);
}

// ============================================
// Navigation
// ============================================
function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            switchPage(item.dataset.page);
        });
    });
}

function switchPage(page) {
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelector(`[data-page="${page}"]`)?.classList.add('active');
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(`page-${page}`)?.classList.add('active');
    closeMobileMenu();
    renderPage(page);
}

function setupMobileMenu() {
    document.getElementById('menu-toggle').addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('open');
        document.getElementById('sidebar-overlay').classList.toggle('show');
    });
    document.getElementById('sidebar-overlay').addEventListener('click', closeMobileMenu);
}

function closeMobileMenu() {
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('sidebar-overlay').classList.remove('show');
}

// ============================================
// Data Loading
// ============================================
async function loadData() {
    try {
        const resp = await fetch('dashboard_data.json');
        DATA = await resp.json();
        renderPage('overview');
    } catch (err) {
        console.error('Failed to load data:', err);
        document.getElementById('main-content').innerHTML =
            `<div style="text-align:center;padding:60px;"><h2 style="color:#ef4444">Error Loading Data</h2><p>Could not load dashboard_data.json</p><pre>${err.message}</pre></div>`;
    }
}

// ============================================
// Page Renderers
// ============================================
const rendered = {};

function renderPage(page) {
    if (!DATA) return;
    if (rendered[page]) return;
    rendered[page] = true;
    const fn = { overview: renderOverview, performance: renderPerformance, investors: renderInvestors, sip: renderSipTrends, risk: renderRiskAnalytics };
    fn[page]?.();
}

// ============================================
// PAGE 1: Industry Overview
// ============================================
function renderOverview() {
    const k = DATA.kpis;
    const C = getColors();

    document.getElementById('kpi-overview').innerHTML = `
        <div class="kpi-card"><div class="kpi-label">Total AUM</div><div class="kpi-value accent">${fmtCr(k.total_aum_crore)}</div><div class="kpi-sub">Across ${k.fund_houses} fund houses</div></div>
        <div class="kpi-card"><div class="kpi-label">Monthly SIP Inflow</div><div class="kpi-value">₹${fmt(k.latest_sip_inflow)}K Cr</div><div class="kpi-sub">Latest monthly figure</div></div>
        <div class="kpi-card"><div class="kpi-label">Total Folios</div><div class="kpi-value">${k.total_folios_crore} Cr</div><div class="kpi-sub">Investor accounts</div></div>
        <div class="kpi-card"><div class="kpi-label">Active Schemes</div><div class="kpi-value accent">${fmt(k.total_schemes)}</div><div class="kpi-sub">In our analysis</div></div>
    `;

    // AUM Trend
    const aum = DATA.aum_trend;
    const ctx1 = document.getElementById('chart-aum-trend').getContext('2d');
    charts['aum-trend'] = new Chart(ctx1, {
        type: 'line',
        data: {
            labels: aum.map(d => d.date),
            datasets: [{
                label: 'Total AUM (₹ Cr)',
                data: aum.map(d => d.total_aum),
                borderColor: C.primary,
                backgroundColor: gradient(ctx1, C.primaryAlpha, 'rgba(0,0,0,0)'),
                fill: true, borderWidth: 2.5,
                pointRadius: 4, pointBackgroundColor: C.primary,
                pointBorderColor: C.cardBg, pointBorderWidth: 2,
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => `AUM: ₹${fmt(ctx.raw)} Cr` } } },
            scales: { x: { ticks: { maxTicksLimit: 8 } }, y: { ticks: { callback: v => (v/1e6).toFixed(1)+'M Cr' } } }
        }
    });

    // AUM by Fund House
    const houses = DATA.aum_by_house;
    charts['aum-house'] = new Chart(document.getElementById('chart-aum-house'), {
        type: 'bar',
        data: {
            labels: houses.map(d => d.fund_house.replace(' Mutual Fund','').replace(' MF','')),
            datasets: [{
                label: 'AUM (₹ Cr)',
                data: houses.map(d => d.aum_crore),
                backgroundColor: C.palette.slice(0, houses.length).map(c => c + '88'),
                borderColor: C.palette.slice(0, houses.length),
                borderWidth: 1.5,
            }]
        },
        options: {
            indexAxis: 'y', responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => `AUM: ₹${fmt(ctx.raw)} Cr | ${houses[ctx.dataIndex].num_schemes} schemes` } } },
            scales: { x: { ticks: { callback: v => (v/1e5).toFixed(0)+'L Cr' } } }
        }
    });

    // Folio Trend
    const folio = DATA.folio_trend;
    const ctx3 = document.getElementById('chart-folio-trend').getContext('2d');
    charts['folio-trend'] = new Chart(ctx3, {
        type: 'line',
        data: {
            labels: folio.map(d => d.month),
            datasets: [
                { label: 'Total (Cr)', data: folio.map(d => d.total_folios_crore), borderColor: C.purple, backgroundColor: gradient(ctx3, C.purple+'33', 'rgba(0,0,0,0)'), fill: true, borderWidth: 2.5 },
                { label: 'Equity (Cr)', data: folio.map(d => d.equity_folios_crore), borderColor: C.primary, borderWidth: 2, borderDash: [5,3] },
                { label: 'Debt (Cr)', data: folio.map(d => d.debt_folios_crore), borderColor: C.yellow, borderWidth: 2, borderDash: [5,3] }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.raw} Cr` } } },
            scales: { x: { ticks: { maxTicksLimit: 8 } }, y: { ticks: { callback: v => v+' Cr' } } }
        }
    });

    // Category Inflows
    const catI = DATA.category_inflow_totals.slice(0, 10);
    charts['category-inflows'] = new Chart(document.getElementById('chart-category-inflows'), {
        type: 'bar',
        data: {
            labels: catI.map(d => d.category),
            datasets: [{
                label: 'Net Inflow (₹ Cr)',
                data: catI.map(d => d.total),
                backgroundColor: C.palette.slice(0, catI.length).map(c => c + '77'),
                borderColor: C.palette.slice(0, catI.length),
                borderWidth: 1.5,
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => `Net Inflow: ₹${fmt(ctx.raw)} Cr` } } },
            scales: { x: { ticks: { maxRotation: 45, minRotation: 30, font: { size: 10 } } }, y: { ticks: { callback: v => (v/1e3).toFixed(0)+'K Cr' } } }
        }
    });
}

// ============================================
// PAGE 2: Fund Performance
// ============================================
function renderPerformance() {
    const C = getColors();
    const perf = DATA.fund_performance;

    // Populate filters
    const addOpts = (id, vals) => { const el = document.getElementById(id); vals.forEach(v => { const o = document.createElement('option'); o.value = v; o.textContent = v; el.appendChild(o); }); };
    addOpts('filter-fund-house', [...new Set(perf.map(d => d.fund_house))].sort());
    addOpts('filter-category', [...new Set(perf.map(d => d.category))].sort());
    addOpts('filter-plan', [...new Set(perf.map(d => d.plan))].sort());
    addOpts('filter-risk', [...new Set(perf.map(d => d.risk_grade).filter(Boolean))].sort());

    // Scorecard
    const tbody = document.getElementById('scorecard-tbody');
    tbody.innerHTML = DATA.scorecard.map(d => {
        const cls = d.composite_score >= 75 ? 'excellent' : d.composite_score >= 55 ? 'good' : d.composite_score >= 35 ? 'average' : 'below';
        return `<tr>
            <td>${d.rank}</td>
            <td title="${d.scheme_name}">${shortName(d.scheme_name, 26)}</td>
            <td>${d.category}</td>
            <td class="${d.cagr_1yr>=0?'positive':'negative'}">${d.cagr_1yr.toFixed(1)}%</td>
            <td>${d.expense_ratio}%</td>
            <td>${d.sharpe_ratio.toFixed(2)}</td>
            <td><span class="score-pill ${cls}">${d.composite_score.toFixed(0)}</span></td>
        </tr>`;
    }).join('');

    // Risk-Return Bubble
    const scatter = DATA.risk_scatter;
    const cats = [...new Set(scatter.map(d => d.category))];
    charts['risk-return'] = new Chart(document.getElementById('chart-risk-return'), {
        type: 'bubble',
        data: {
            datasets: cats.map((cat, i) => ({
                label: cat,
                data: scatter.filter(d => d.category===cat).map(d => ({ x: d.return_3yr, y: d.std_dev, r: Math.max(5, Math.min(22, (d.aum||1000)/30000)), name: d.name, aum: d.aum })),
                backgroundColor: C.palette[i % C.palette.length] + '55',
                borderColor: C.palette[i % C.palette.length],
                borderWidth: 1.5,
            }))
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { tooltip: { callbacks: { label: ctx => { const d = ctx.raw; return `${d.name} | Ret: ${d.x.toFixed(1)}% | Risk: ${d.y.toFixed(1)}% | AUM: ₹${fmt(d.aum)} Cr`; } } } },
            scales: {
                x: { title: { display: true, text: '3-Yr Return (%)', color: C.textSecondary }, ticks: { callback: v => v+'%' } },
                y: { title: { display: true, text: 'Risk / Std Dev (%)', color: C.textSecondary }, ticks: { callback: v => v+'%' } }
            }
        }
    });

    // NAV Trend
    const navData = DATA.nav_trend;
    const nifty = DATA.nifty_trend;
    const funds = [...new Set(navData.map(d => d.scheme_name))];
    const datasets = funds.map((fund, i) => {
        const fd = navData.filter(d => d.scheme_name===fund);
        const base = fd[0]?.nav || 1;
        return { label: shortName(fund, 28), data: fd.map(d => ({ x: d.date, y: ((d.nav/base)*100).toFixed(2) })), borderColor: C.palette[i % C.palette.length], borderWidth: 2, fill: false, pointRadius: 0, pointHoverRadius: 4 };
    });
    if (nifty.length) {
        const nb = nifty[0]?.value || 1;
        datasets.push({ label: 'NIFTY 50', data: nifty.map(d => ({ x: d.date, y: ((d.value/nb)*100).toFixed(2) })), borderColor: C.muted, borderWidth: 2, borderDash: [6,3], fill: false, pointRadius: 0 });
    }
    charts['nav-trend'] = new Chart(document.getElementById('chart-nav-trend'), {
        type: 'line',
        data: { datasets },
        options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: { legend: { position: 'top', labels: { font: { size: 11 } } }, tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.raw.y}` } } },
            scales: {
                x: { type: 'category', labels: [...new Set(navData.map(d => d.date))], ticks: { maxTicksLimit: 10, font: { size: 10 } } },
                y: { title: { display: true, text: 'Normalized (Base = 100)', color: C.textSecondary } }
            }
        }
    });
}

// ============================================
// PAGE 3: Investor Analytics
// ============================================
function renderInvestors() {
    const k = DATA.kpis;
    const C = getColors();
    const totalInv = k.sip_total + k.lumpsum_total;

    document.getElementById('kpi-investors').innerHTML = `
        <div class="kpi-card"><div class="kpi-label">Total Investors</div><div class="kpi-value accent">${fmt(k.total_investors)}</div><div class="kpi-sub">Unique investor IDs</div></div>
        <div class="kpi-card"><div class="kpi-label">Total Transactions</div><div class="kpi-value">${fmt(k.total_transactions)}</div><div class="kpi-sub">SIP + Lumpsum + Redemption</div></div>
        <div class="kpi-card"><div class="kpi-label">Total Invested</div><div class="kpi-value accent">${fmtMoney(totalInv)}</div><div class="kpi-sub">SIP: ${fmtMoney(k.sip_total)} + Lump: ${fmtMoney(k.lumpsum_total)}</div></div>
        <div class="kpi-card"><div class="kpi-label">Redemptions</div><div class="kpi-value" style="color:${C.negative}">${fmtMoney(k.redemption_total)}</div><div class="kpi-sub">${fmt(k.redemption_count)} transactions</div></div>
    `;

    // State
    const states = DATA.state_transactions.slice(0, 8);
    charts['state-txn'] = new Chart(document.getElementById('chart-state-txn'), {
        type: 'bar',
        data: {
            labels: states.map(d => d.state),
            datasets: [{ data: states.map(d => d.total_amount), backgroundColor: C.palette.slice(0,8).map(c=>c+'77'), borderColor: C.palette.slice(0,8), borderWidth: 1.5 }]
        },
        options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => `Amount: ${fmtMoney(ctx.raw)} | ${fmt(states[ctx.dataIndex].count)} txns` } } }, scales: { x: { ticks: { callback: v => fmtMoney(v) } } } }
    });

    // Doughnut — Txn Split
    const split = DATA.txn_type_split;
    const dColors = [C.primary, C.yellow, C.red];
    charts['txn-split'] = new Chart(document.getElementById('chart-txn-split'), {
        type: 'doughnut',
        data: { labels: split.map(d => d.type), datasets: [{ data: split.map(d => d.total), backgroundColor: dColors.map(c=>c+'99'), borderColor: dColors, borderWidth: 2, hoverOffset: 8 }] },
        options: {
            responsive: true, maintainAspectRatio: false, cutout: '65%',
            plugins: { legend: { position: 'bottom' }, tooltip: { callbacks: { label: ctx => { const tot = split.reduce((a,b)=>a+b.total,0); return `${ctx.label}: ${fmtMoney(ctx.raw)} (${((ctx.raw/tot)*100).toFixed(1)}%)`; } } } }
        },
        plugins: [{
            id: 'centerText',
            afterDraw: chart => {
                const { ctx: c, chartArea } = chart;
                const tot = split.reduce((a,b) => a+b.total, 0);
                const cx = (chartArea.left+chartArea.right)/2, cy = (chartArea.top+chartArea.bottom)/2;
                c.save(); c.textAlign='center'; c.textBaseline='middle';
                c.fillStyle = C.textSecondary; c.font = '500 11px Inter'; c.fillText('Total:', cx, cy-12);
                c.fillStyle = C.text; c.font = '700 16px Inter'; c.fillText(fmtMoney(tot), cx, cy+10);
                c.restore();
            }
        }]
    });

    // Age group
    const age = DATA.age_group;
    charts['age-sip'] = new Chart(document.getElementById('chart-age-sip'), {
        type: 'bar',
        data: {
            labels: age.map(d => d.age_group),
            datasets: [{ label: 'Avg Amount (₹)', data: age.map(d => d.avg_amount), backgroundColor: age.map((_,i) => { const ops = ['44','55','88','66','44']; return C.primary + ops[i%5]; }), borderColor: C.primary, borderWidth: 1.5 }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => `Avg: ₹${fmt(ctx.raw)} | ${fmt(age[ctx.dataIndex].count)} txns` } } }, scales: { y: { ticks: { callback: v => '₹'+fmt(v) } } } }
    });

    // Monthly Volume
    const mo = DATA.monthly_transactions;
    const ctx5 = document.getElementById('chart-monthly-vol').getContext('2d');
    charts['monthly-vol'] = new Chart(ctx5, {
        type: 'line',
        data: { labels: mo.map(d => d.month), datasets: [{ label: 'Count', data: mo.map(d => d.count), borderColor: C.primary, backgroundColor: gradient(ctx5, C.primaryAlpha, 'rgba(0,0,0,0)'), fill: true, borderWidth: 2.5, pointRadius: 3, pointBackgroundColor: C.primary }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => `Volume: ${fmt(ctx.raw)} | Total: ${fmtMoney(mo[ctx.dataIndex].total)}` } } }, scales: { x: { ticks: { maxTicksLimit: 10, font: { size: 10 } } }, y: { ticks: { callback: v => (v/1e3).toFixed(0)+'K' } } } }
    });

    // Gender
    charts['gender'] = new Chart(document.getElementById('chart-gender'), {
        type: 'doughnut',
        data: { labels: DATA.gender_distribution.map(d => d.gender), datasets: [{ data: DATA.gender_distribution.map(d => d.count), backgroundColor: [C.pink+'88', C.primary+'88'], borderColor: [C.pink, C.primary], borderWidth: 2, hoverOffset: 6 }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '60%', plugins: { legend: { position: 'bottom' }, tooltip: { callbacks: { label: ctx => { const t = DATA.gender_distribution.reduce((a,b)=>a+b.count,0); return `${ctx.label}: ${fmt(ctx.raw)} (${((ctx.raw/t)*100).toFixed(1)}%)`; } } } } }
    });

    // City Tier
    charts['city-tier'] = new Chart(document.getElementById('chart-city-tier'), {
        type: 'doughnut',
        data: { labels: DATA.city_tier.map(d => d.city_tier), datasets: [{ data: DATA.city_tier.map(d => d.count), backgroundColor: [C.primary+'88', C.purple+'88', C.yellow+'88'], borderColor: [C.primary, C.purple, C.yellow], borderWidth: 2, hoverOffset: 6 }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '60%', plugins: { legend: { position: 'bottom' }, tooltip: { callbacks: { label: ctx => `${ctx.label}: ${fmt(ctx.raw)} txns` } } } }
    });

    // Payment
    charts['payment'] = new Chart(document.getElementById('chart-payment'), {
        type: 'doughnut',
        data: { labels: DATA.payment_mode.map(d => d.payment_mode), datasets: [{ data: DATA.payment_mode.map(d => d.count), backgroundColor: [C.green+'88', C.orange+'88', C.lavender+'88', C.red+'88'], borderColor: [C.green, C.orange, C.lavender, C.red], borderWidth: 2, hoverOffset: 6 }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '60%', plugins: { legend: { position: 'bottom' }, tooltip: { callbacks: { label: ctx => `${ctx.label}: ${fmt(ctx.raw)} txns` } } } }
    });
}

// ============================================
// PAGE 4: SIP & Market Trends
// ============================================
function renderSipTrends() {
    const sip = DATA.sip_trend;
    const C = getColors();
    const latest = sip[sip.length-1], earliest = sip[0];
    const growth = ((latest.sip_inflow_crore - earliest.sip_inflow_crore) / earliest.sip_inflow_crore * 100).toFixed(1);

    document.getElementById('kpi-sip').innerHTML = `
        <div class="kpi-card"><div class="kpi-label">Latest SIP Inflow</div><div class="kpi-value accent">₹${fmt(latest.sip_inflow_crore)} Cr</div><div class="kpi-sub">${latest.month}</div></div>
        <div class="kpi-card"><div class="kpi-label">Active SIP Accounts</div><div class="kpi-value">${latest.active_sip_accounts_crore} Cr</div><div class="kpi-sub"><span class="pulse-dot"></span>Live tracking</div></div>
        <div class="kpi-card"><div class="kpi-label">SIP AUM</div><div class="kpi-value">₹${latest.sip_aum_lakh_crore}L Cr</div><div class="kpi-sub">Assets under SIP</div></div>
        <div class="kpi-card"><div class="kpi-label">Growth Since 2022</div><div class="kpi-value" style="color:${C.positive}">+${growth}%</div><div class="kpi-sub">SIP inflow growth</div></div>
    `;

    // SIP vs NIFTY dual axis
    const niftyMap = {};
    DATA.nifty_trend.forEach(d => { niftyMap[d.date.substring(0,7)] = d.value; });
    const sipMonths = sip.map(d => d.month);
    const niftyForSip = sipMonths.map(m => { const ks = Object.keys(niftyMap).filter(k => k <= m+'-31').sort(); return ks.length ? niftyMap[ks[ks.length-1]] : null; });

    charts['sip-nifty'] = new Chart(document.getElementById('chart-sip-nifty'), {
        type: 'bar',
        data: {
            labels: sipMonths,
            datasets: [
                { type: 'bar', label: 'Monthly SIP Inflows (₹ Cr)', data: sip.map(d => d.sip_inflow_crore), backgroundColor: sip.map((_,i) => { const r = i/sip.length; return `rgba(37, ${Math.round(80+r*100)}, ${Math.round(180+r*55)}, 0.75)`; }), borderColor: C.primary, borderWidth: 1, yAxisID: 'y', order: 2 },
                { type: 'line', label: 'Nifty 50 Index', data: niftyForSip, borderColor: C.green, backgroundColor: 'transparent', borderWidth: 2.5, pointRadius: 3, pointBackgroundColor: C.green, yAxisID: 'y1', order: 1 }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: { legend: { position: 'top' }, tooltip: { callbacks: { label: ctx => ctx.datasetIndex===0 ? `SIP: ₹${fmt(ctx.raw)} Cr` : `NIFTY: ${fmt(ctx.raw)}` } } },
            scales: {
                x: { ticks: { maxTicksLimit: 12, font: { size: 10 } } },
                y: { position: 'left', title: { display: true, text: 'SIP Inflow (₹ Cr)', color: C.primary }, ticks: { color: C.primary, callback: v => (v/1e3).toFixed(0)+'K' } },
                y1: { position: 'right', title: { display: true, text: 'Nifty 50', color: C.green }, ticks: { color: C.green, callback: v => (v/1e3).toFixed(0)+'K' }, grid: { display: false } }
            }
        }
    });

    // SIP Account Growth
    const ctxA = document.getElementById('chart-sip-accounts').getContext('2d');
    charts['sip-accounts'] = new Chart(ctxA, {
        type: 'line',
        data: { labels: sip.map(d => d.month), datasets: [{ label: 'Active SIP (Cr)', data: sip.map(d => d.active_sip_accounts_crore), borderColor: C.primary, backgroundColor: gradient(ctxA, C.primaryAlpha, 'rgba(0,0,0,0)'), fill: true, borderWidth: 2.5, pointRadius: 3, pointBackgroundColor: C.primary }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => `Active: ${ctx.raw} Cr` } } }, scales: { x: { ticks: { maxTicksLimit: 10 } }, y: { ticks: { callback: v => v+' Cr' } } } }
    });

    // Top Categories
    const topC = DATA.category_inflow_totals.slice(0, 5);
    charts['top-categories'] = new Chart(document.getElementById('chart-top-categories'), {
        type: 'bar',
        data: { labels: topC.map(d => d.category), datasets: [{ data: topC.map(d => d.total), backgroundColor: C.palette.slice(0,5).map(c=>c+'77'), borderColor: C.palette.slice(0,5), borderWidth: 1.5 }] },
        options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => `Inflow: ₹${fmt(ctx.raw)} Cr` } } }, scales: { x: { ticks: { callback: v => (v/1e3).toFixed(0)+'K Cr' } } } }
    });
}

// ============================================
// PAGE 5: Risk Analytics
// ============================================
function renderRiskAnalytics() {
    const C = getColors();
    const varD = DATA.var_cvar;
    const sorted = [...varD].sort((a,b) => a.var_95 - b.var_95);

    const barColor = (v, t) => {
        if (t === 'var') return v < -2 ? C.red+'88' : v < -1 ? C.orange+'88' : C.green+'88';
        return v < -2.5 ? C.red+'88' : v < -1.5 ? C.orange+'88' : C.green+'88';
    };
    const barBorder = (v, t) => {
        if (t === 'var') return v < -2 ? C.red : v < -1 ? C.orange : C.green;
        return v < -2.5 ? C.red : v < -1.5 ? C.orange : C.green;
    };

    charts['var'] = new Chart(document.getElementById('chart-var'), {
        type: 'bar',
        data: { labels: sorted.map(d => shortName(d.scheme_name,22)), datasets: [{ label: 'VaR 95%', data: sorted.map(d => d.var_95), backgroundColor: sorted.map(d => barColor(d.var_95,'var')), borderColor: sorted.map(d => barBorder(d.var_95,'var')), borderWidth: 1.5 }] },
        options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => `VaR: ${ctx.raw.toFixed(4)}%` } } }, scales: { x: { ticks: { callback: v => v.toFixed(1)+'%' }, title: { display: true, text: 'Daily VaR (%)', color: C.textSecondary } }, y: { ticks: { font: { size: 10 } } } } }
    });

    const sortedC = [...varD].sort((a,b) => a.cvar_95 - b.cvar_95);
    charts['cvar'] = new Chart(document.getElementById('chart-cvar'), {
        type: 'bar',
        data: { labels: sortedC.map(d => shortName(d.scheme_name,22)), datasets: [{ label: 'CVaR 95%', data: sortedC.map(d => d.cvar_95), backgroundColor: sortedC.map(d => barColor(d.cvar_95,'cvar')), borderColor: sortedC.map(d => barBorder(d.cvar_95,'cvar')), borderWidth: 1.5 }] },
        options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => `CVaR: ${ctx.raw.toFixed(4)}%` } } }, scales: { x: { ticks: { callback: v => v.toFixed(1)+'%' }, title: { display: true, text: 'Daily CVaR / Expected Shortfall (%)', color: C.textSecondary } }, y: { ticks: { font: { size: 10 } } } } }
    });

    // Risk Grade
    const grades = {};
    DATA.fund_performance.forEach(d => { const g = d.risk_grade || 'Unknown'; grades[g] = (grades[g]||0) + 1; });
    const gLabels = Object.keys(grades).sort();
    const gColors = { Low: C.green, Moderate: C.yellow, 'Moderately High': C.orange, High: C.red, 'Very High': '#b91c1c', Unknown: '#6b7280' };

    charts['risk-grade'] = new Chart(document.getElementById('chart-risk-grade'), {
        type: 'doughnut',
        data: { labels: gLabels, datasets: [{ data: gLabels.map(g => grades[g]), backgroundColor: gLabels.map(g => (gColors[g]||C.lavender)+'88'), borderColor: gLabels.map(g => gColors[g]||C.lavender), borderWidth: 2, hoverOffset: 8 }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '55%', plugins: { legend: { position: 'bottom' }, tooltip: { callbacks: { label: ctx => `${ctx.label}: ${ctx.raw} funds` } } } }
    });
}
