/**
 * FinSight - Financial Analytics Dashboard
 * Client-side JavaScript for Chart.js visualizations and ticker animations.
 */

// === Chart.js Global Configuration ===
Chart.defaults.color = '#8b949e';
Chart.defaults.borderColor = '#30363d';
Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif";

const COLORS = {
    gain: '#3fb950',
    loss: '#f85149',
    blue: '#58a6ff',
    purple: '#bc8cff',
    yellow: '#d29922',
    orange: '#db6d28',
    cyan: '#39d2c0',
    pink: '#f778ba',
    text: '#e6edf3',
    muted: '#6e7681',
    bg: '#1c2128',
    grid: '#21262d',
};

const CHART_COLORS = [
    COLORS.blue, COLORS.gain, COLORS.purple, COLORS.yellow,
    COLORS.orange, COLORS.cyan, COLORS.pink, COLORS.loss,
];

// === Ticker Animation ===
function initTicker() {
    fetch('/api/stocks')
        .then(r => r.json())
        .then(data => {
            const tickerEl = document.getElementById('navTicker');
            if (!tickerEl || !data.stocks) return;

            const items = data.stocks.map(s => {
                const change = s.change_percent;
                const cls = change > 0 ? 'gain' : change < 0 ? 'loss' : '';
                const sign = change > 0 ? '+' : '';
                return `<span class="ticker-item"><strong>${s.symbol}</strong> $${s.current_price.toFixed(2)} <span class="${cls}">${sign}${change}%</span></span>`;
            });

            tickerEl.innerHTML = items.join(' &nbsp;&bull;&nbsp; ');

            // Scroll animation
            let scrollPos = 0;
            const scrollWidth = tickerEl.scrollWidth;
            const containerWidth = tickerEl.clientWidth;

            if (scrollWidth > containerWidth) {
                setInterval(() => {
                    scrollPos += 1;
                    if (scrollPos > scrollWidth - containerWidth) scrollPos = 0;
                    tickerEl.scrollLeft = scrollPos;
                }, 30);
            }
        })
        .catch(() => {});
}

// === Price Chart (OHLC bars with SMA/Bollinger overlays) ===
function renderPriceChart(ohlcv) {
    const ctx = document.getElementById('priceChart');
    if (!ctx) return;

    const labels = ohlcv.map(d => d.date);
    const closes = ohlcv.map(d => d.close);
    const highs = ohlcv.map(d => d.high);
    const lows = ohlcv.map(d => d.low);

    // Compute SMA 20 for overlay
    const sma20 = [];
    for (let i = 0; i < closes.length; i++) {
        if (i < 19) { sma20.push(null); continue; }
        let sum = 0;
        for (let j = i - 19; j <= i; j++) sum += closes[j];
        sma20.push(sum / 20);
    }

    // Compute Bollinger Bands
    const bbUpper = [];
    const bbLower = [];
    for (let i = 0; i < closes.length; i++) {
        if (i < 19) { bbUpper.push(null); bbLower.push(null); continue; }
        const window = closes.slice(i - 19, i + 1);
        const mean = window.reduce((a, b) => a + b, 0) / 20;
        const variance = window.reduce((a, b) => a + (b - mean) ** 2, 0) / 20;
        const std = Math.sqrt(variance);
        bbUpper.push(mean + 2 * std);
        bbLower.push(mean - 2 * std);
    }

    // OHLC bar colors
    const barColors = ohlcv.map(d => d.close >= d.open ? COLORS.gain : COLORS.loss);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Close',
                    data: closes,
                    type: 'line',
                    borderColor: COLORS.blue,
                    backgroundColor: 'transparent',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    tension: 0.1,
                    order: 1,
                },
                {
                    label: 'SMA 20',
                    data: sma20,
                    type: 'line',
                    borderColor: COLORS.yellow,
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    borderDash: [4, 4],
                    pointRadius: 0,
                    order: 2,
                },
                {
                    label: 'BB Upper',
                    data: bbUpper,
                    type: 'line',
                    borderColor: 'rgba(188, 140, 255, 0.3)',
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    pointRadius: 0,
                    order: 3,
                },
                {
                    label: 'BB Lower',
                    data: bbLower,
                    type: 'line',
                    borderColor: 'rgba(188, 140, 255, 0.3)',
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: { target: 2, above: 'rgba(188, 140, 255, 0.04)' },
                    order: 4,
                },
                {
                    label: 'High',
                    data: highs,
                    type: 'bar',
                    backgroundColor: barColors.map(c => c + '33'),
                    borderColor: barColors,
                    borderWidth: 1,
                    barPercentage: 0.3,
                    order: 5,
                    hidden: true,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { display: true, position: 'top', labels: { boxWidth: 12, padding: 12 } },
                tooltip: {
                    callbacks: {
                        afterBody: function(items) {
                            const idx = items[0].dataIndex;
                            const bar = ohlcv[idx];
                            return [
                                `Open: $${bar.open.toFixed(2)}`,
                                `High: $${bar.high.toFixed(2)}`,
                                `Low: $${bar.low.toFixed(2)}`,
                                `Close: $${bar.close.toFixed(2)}`,
                                `Volume: ${bar.volume.toLocaleString()}`,
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: COLORS.grid },
                    ticks: { maxTicksLimit: 12, maxRotation: 0 }
                },
                y: {
                    grid: { color: COLORS.grid },
                    ticks: { callback: v => '$' + v.toFixed(0) }
                },
            },
        },
    });
}

// === Volume Chart ===
function renderVolumeChart(ohlcv) {
    const ctx = document.getElementById('volumeChart');
    if (!ctx) return;

    const labels = ohlcv.map(d => d.date);
    const volumes = ohlcv.map(d => d.volume);
    const colors = ohlcv.map(d => d.close >= d.open ? COLORS.gain + '80' : COLORS.loss + '80');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Volume',
                data: volumes,
                backgroundColor: colors,
                borderWidth: 0,
                barPercentage: 0.8,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false }, ticks: { maxTicksLimit: 12, maxRotation: 0 } },
                y: {
                    grid: { color: COLORS.grid },
                    ticks: { callback: v => (v / 1e6).toFixed(0) + 'M' }
                },
            },
        },
    });
}

// === RSI Chart ===
function renderRSIChart(dates, rsiData) {
    const ctx = document.getElementById('rsiChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'RSI (14)',
                data: rsiData,
                borderColor: COLORS.purple,
                backgroundColor: 'transparent',
                borderWidth: 1.5,
                pointRadius: 0,
                tension: 0.2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                annotation: {
                    annotations: {
                        overbought: { type: 'line', yMin: 70, yMax: 70, borderColor: COLORS.loss + '60', borderWidth: 1, borderDash: [5, 5] },
                        oversold: { type: 'line', yMin: 30, yMax: 30, borderColor: COLORS.gain + '60', borderWidth: 1, borderDash: [5, 5] },
                    }
                }
            },
            scales: {
                x: { grid: { display: false }, ticks: { maxTicksLimit: 12, maxRotation: 0 } },
                y: { min: 0, max: 100, grid: { color: COLORS.grid } },
            },
        },
    });

    // Draw overbought/oversold lines manually since annotation plugin may not be loaded
    const chart = Chart.getChart(ctx);
    if (chart) {
        const origDraw = chart.draw.bind(chart);
        chart.draw = function() {
            origDraw();
            const yAxis = chart.scales.y;
            const xAxis = chart.scales.x;
            const ctxCanvas = chart.ctx;
            [30, 70].forEach(level => {
                const y = yAxis.getPixelForValue(level);
                ctxCanvas.save();
                ctxCanvas.setLineDash([5, 5]);
                ctxCanvas.strokeStyle = level === 70 ? COLORS.loss + '60' : COLORS.gain + '60';
                ctxCanvas.lineWidth = 1;
                ctxCanvas.beginPath();
                ctxCanvas.moveTo(xAxis.left, y);
                ctxCanvas.lineTo(xAxis.right, y);
                ctxCanvas.stroke();
                ctxCanvas.restore();
            });
        };
        chart.draw();
    }
}

// === MACD Chart ===
function renderMACDChart(dates, macdData) {
    const ctx = document.getElementById('macdChart');
    if (!ctx) return;

    const histColors = macdData.histogram.map(v => {
        if (v === null) return COLORS.muted;
        return v >= 0 ? COLORS.gain + '80' : COLORS.loss + '80';
    });

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'MACD',
                    data: macdData.macd_line,
                    type: 'line',
                    borderColor: COLORS.blue,
                    backgroundColor: 'transparent',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    order: 1,
                },
                {
                    label: 'Signal',
                    data: macdData.signal_line,
                    type: 'line',
                    borderColor: COLORS.orange,
                    backgroundColor: 'transparent',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    order: 2,
                },
                {
                    label: 'Histogram',
                    data: macdData.histogram,
                    backgroundColor: histColors,
                    borderWidth: 0,
                    barPercentage: 0.6,
                    order: 3,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: true, position: 'top', labels: { boxWidth: 12 } } },
            scales: {
                x: { grid: { display: false }, ticks: { maxTicksLimit: 12, maxRotation: 0 } },
                y: { grid: { color: COLORS.grid } },
            },
        },
    });
}

// === Allocation Donut Chart ===
function renderAllocationChart(data) {
    const ctx = document.getElementById('allocationChart');
    if (!ctx) return;

    const labels = [];
    const values = [];
    const colors = [];

    if (data.stock_allocation) {
        data.stock_allocation.forEach((item, i) => {
            labels.push(item.symbol);
            values.push(item.market_value);
            colors.push(CHART_COLORS[i % CHART_COLORS.length]);
        });
    }

    // Add cash
    if (data.cash_balance > 0) {
        labels.push('Cash');
        values.push(data.cash_balance);
        colors.push(COLORS.muted);
    }

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderColor: '#0d1117',
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: { padding: 12, boxWidth: 12, font: { size: 11 } }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = ((context.parsed / total) * 100).toFixed(1);
                            return `${context.label}: $${context.parsed.toLocaleString(undefined, {minimumFractionDigits: 2})} (${pct}%)`;
                        }
                    }
                }
            },
        },
    });
}

// === Sentiment Bar Chart ===
function renderSentimentChart(summary) {
    const ctx = document.getElementById('sentimentChart');
    if (!ctx) return;

    const labels = summary.map(s => s.symbol);
    const scores = summary.map(s => s.avg_score);
    const colors = scores.map(s => s > 0.15 ? COLORS.gain : s < -0.15 ? COLORS.loss : COLORS.muted);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Sentiment Score',
                data: scores,
                backgroundColor: colors.map(c => c + '80'),
                borderColor: colors,
                borderWidth: 1,
                barPercentage: 0.6,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
            },
            scales: {
                x: {
                    grid: { color: COLORS.grid },
                    min: -1,
                    max: 1,
                    ticks: {
                        callback: function(v) {
                            if (v === -1) return 'Bearish';
                            if (v === 0) return 'Neutral';
                            if (v === 1) return 'Bullish';
                            return v;
                        }
                    }
                },
                y: {
                    grid: { display: false },
                    ticks: { font: { family: "'SF Mono', monospace", size: 11 } }
                },
            },
        },
    });
}

// === Initialize on page load ===
document.addEventListener('DOMContentLoaded', function() {
    initTicker();
});
