import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

/**
 * CitationsBarChart component renders a bar chart of citations per year for a given metric.
 *
 * @param metric
 * @param allMetrics
 * @returns {React.JSX.Element}
 * @constructor
 */
export default function CitationsBarChart({ metric }) {
    if (!metric || !metric.cites_per_year) {
        return (
            <div className="chart-empty-state">
                <div className="chart-empty-text">
                    No citations data available for this source
                </div>
            </div>
        );
    }

    let citesPerYear = metric.cites_per_year;
    if (typeof citesPerYear === 'string') {
        try {
            citesPerYear = JSON.parse(citesPerYear);
        } catch (e) {
            return (
                <div className="chart-empty-state">
                    <div className="chart-empty-text">
                        Error parsing citations data
                    </div>
                </div>
            );
        }
    }

    if (typeof citesPerYear !== 'object' || citesPerYear === null) {
        return (
            <div className="chart-empty-state">
                <div className="chart-empty-text">
                    Invalid citations data format
                </div>
            </div>
        );
    }

    const chartData = Object.entries(citesPerYear)
        .map(([year, citations]) => ({
            year: parseInt(year),
            citations: parseInt(citations) || 0,
        }))
        .filter(item => !isNaN(item.year)) // Filter out invalid years
        .sort((a, b) => a.year - b.year);

    if (chartData.length === 0) {
        return (
            <div className="chart-empty-state">
                <div className="chart-empty-text">
                    No citations data available for this source
                </div>
            </div>
        );
    }

    return (
        <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
                <BarChart
                    data={chartData}
                    margin={{ top: 20, right: 30, left: 0, bottom: 20 }}
                >
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis
                        dataKey="year"
                        tick={{ fill: 'var(--text-3)', fontSize: 12 }}
                        axisLine={{ stroke: 'var(--border)' }}
                    />
                    <YAxis
                        tick={{ fill: 'var(--text-3)', fontSize: 12 }}
                        axisLine={{ stroke: 'var(--border)' }}
                    />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: 'var(--bg-1)',
                            border: '1px solid var(--border)',
                            borderRadius: '6px',
                            color: 'var(--text-1)',
                        }}
                        labelStyle={{ color: 'var(--text-1)' }}
                        formatter={(value) => value.toLocaleString()}
                    />
                    <Legend
                        wrapperStyle={{ color: 'var(--text-2)', fontSize: '12px' }}
                    />
                    <Bar
                        dataKey="citations"
                        fill="var(--primary)"
                        radius={[4, 4, 0, 0]}
                        name="Citations by Year"
                    />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}

