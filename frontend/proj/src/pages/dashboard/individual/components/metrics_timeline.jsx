import { useState, useMemo } from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts';

function getPeriodKey(dateStr, granularity) {
    const d = new Date(dateStr);
    if (granularity === 'month') {
        return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    }
    const jan4 = new Date(d.getFullYear(), 0, 4);
    const week = Math.ceil(((d - jan4) / 86400000 + jan4.getDay() + 1) / 7);
    return `${d.getFullYear()}-W${String(week).padStart(2, '0')}`;
}

function formatPeriodLabel(key, granularity) {
    if (granularity === 'month') {
        const [year, month] = key.split('-');
        return new Date(year, month - 1).toLocaleDateString('en', { month: 'short', year: '2-digit' });
    }
    const [year, week] = key.split('-W');
    return `W${week} '${year.slice(2)}`;
}


function aggregateMetrics(metrics, granularity, selectedSource) {
    if (!metrics?.length)
        return [];

    // 1. filtrar source
    const filtered = selectedSource
        ? metrics.filter(
            m => m.source?.name === selectedSource
        )
        : metrics;

    // 2. latest por dia
    const byDay = {};

    for (const m of filtered) {
        if (!m.date)
            continue;

        const day = new Date(m.date)
            .toISOString()
            .split('T')[0];

        if (
            !byDay[day] ||
            new Date(m.date) > new Date(byDay[day].date)
        ) {
            byDay[day] = m;
        }
    }

    // 3. agrupar por período
    const byPeriod = {};

    for (const m of Object.values(byDay)) {
        const key = getPeriodKey(m.date, granularity);

        if (!byPeriod[key])
            byPeriod[key] = [];

        byPeriod[key].push(m);
    }

    // 4. latest do período
    return Object.entries(byPeriod)
        .map(([key, records]) => {
            const latest = records.reduce((a, b) =>
                new Date(a.date) > new Date(b.date)
                    ? a
                    : b
            );

            return {
                period: key,
                label: formatPeriodLabel(key, granularity),

                h_index: latest.h_index,
                i10_index: latest.i10_index,
                total_citations: latest.total_citations,
                total_publications: latest.total_publications,
                h_index_5y: latest.h_index_5y,
                citations_5y: latest.citations_5y,

                date: latest.date,
            };
        })
        .sort((a, b) =>
            a.period.localeCompare(b.period)
        );
}

const CHART_COLOR = '#2d5986';

function MetricLineChart({ data, dataKey, label, formatter }) {
    if (data.every(d => d[dataKey] == null))
        return null;

    const fmt = formatter ?? ((v) => v?.toLocaleString() ?? '—');

    return (
        <div className="timeline-chart-card">
            <div className="timeline-chart-title">{label}</div>
            <ResponsiveContainer width="100%" height={180}>
                <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                    <XAxis
                        dataKey="label"
                        tick={{ fill: 'var(--text-3)', fontSize: 11 }}
                        axisLine={{ stroke: 'var(--border)' }}
                        tickLine={false}
                        interval="preserveStartEnd"
                    />
                    <YAxis
                        tick={{ fill: 'var(--text-3)', fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                        width={40}
                        tickFormatter={fmt}
                    />
                    <Tooltip
                        contentStyle={{
                            background: 'var(--surface)',
                            border: '1px solid var(--border)',
                            borderRadius: 8,
                            fontSize: 12,
                        }}
                        formatter={(v) => [fmt(v), label]}
                        labelStyle={{ color: 'var(--text-2)', marginBottom: 4 }}
                    />
                    <Line
                        type="monotone"
                        dataKey={dataKey}
                        stroke={CHART_COLOR}
                        strokeWidth={2}
                        dot={{ r: 3, fill: CHART_COLOR, strokeWidth: 0 }}
                        activeDot={{ r: 5 }}
                        connectNulls
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}

const METRICS_CONFIG = [
    { key: 'h_index',            label: 'h-index',               formatter: null },
    { key: 'i10_index',          label: 'i10-index',             formatter: null },
    { key: 'total_citations',    label: 'Total citations',       formatter: (v) => v?.toLocaleString() },
    { key: 'total_publications', label: 'Total publications',    formatter: null },
    { key: 'h_index_5y',         label: 'h-index (5 years)',     formatter: null },
    { key: 'citations_5y',       label: 'Citations (5 years)',   formatter: (v) => v?.toLocaleString() },
];

export default function MetricsTimeline({ allMetrics, selectedSource}) {
    console.log(allMetrics);
    const [granularity, setGranularity] = useState('week');

    const aggregated = useMemo(
        () => aggregateMetrics(
            allMetrics,
            granularity,
            selectedSource
        ),
        [allMetrics, granularity, selectedSource]
    );

    if (!allMetrics?.length)
        return null;

    const visibleMetrics = METRICS_CONFIG.filter(
        m => aggregated.some(d => d[m.key] != null)
    );

    return (
        <div className="card" style={{ marginTop: 24 }}>
            <div className="card-header">
                <h3>Metrics over time</h3>
                <div className="timeline-granularity-toggle">
                    <button
                        className={`source-selector-button ${granularity === 'week' ? 'selected' : ''}`}
                        onClick={() => setGranularity('week')}
                    >
                        Week
                    </button>
                    <button
                        className={`source-selector-button ${granularity === 'month' ? 'selected' : ''}`}
                        onClick={() => setGranularity('month')}
                    >
                        Month
                    </button>
                </div>
            </div>

            {aggregated.length < 2 ? (
                <div className="empty-state" style={{ minHeight: 120 }}>
                    <div className="empty-icon" style={{ fontSize: 20 }}>◎</div>
                    <span>Not enough data points to show a timeline</span>
                </div>
            ) : (
                <div className="timeline-charts-grid">
                    {visibleMetrics.map(m => (
                        <MetricLineChart
                            key={m.key}
                            data={aggregated}
                            dataKey={m.key}
                            label={m.label}
                            formatter={m.formatter}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}