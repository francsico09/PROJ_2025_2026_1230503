import MetricCard from './metric_card.jsx';

export default function IndexMetrics({ metric }) {
    if (!metric) {
        return (
            <div className="chart-empty-state">
                <div className="chart-empty-text">
                    No data available
                </div>
            </div>
        );
    }

    return (
        <div className="metrics-grid metrics-grid-4col">
            <MetricCard
                label="h-Index"
                value={metric.h_index}
                variant="primary"
            />
            <MetricCard
                label="h-Index (5y)"
                value={metric.h_index_5y}
                variant="default"
            />
            <MetricCard
                label="i10-Index"
                value={metric.i10_index}
                variant="primary"
            />
            <MetricCard
                label="i10-Index (5y)"
                value={metric.i10_index_5y}
                variant="default"
            />
        </div>
    );
}

