import MetricCard from './metric_card.jsx';

/**
 * CitationsSummary is a component that displays a summary of citation metrics for a researcher.
 *
 * @param metric
 * @returns {React.JSX.Element}
 * @constructor
 */
export default function CitationsSummary({ metric }) {
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
        <div className="metrics-grid metrics-grid-3col">
            <MetricCard
                label="Total Citations"
                value={metric.total_citations}
                subtitle={metric.extracted_at ? `as of ${new Date(metric.extracted_at).toLocaleDateString()}` : ''}
                variant="primary"
            />
            <MetricCard
                label="Citations (5y)"
                value={metric.citations_5y}
                variant="default"
            />
            <MetricCard
                label="Total Publications"
                value={metric.total_publications}
                subtitle={metric.extracted_at ? `as of ${new Date(metric.extracted_at).toLocaleDateString()}` : ''}
                variant="default"
            />
        </div>
    );
}

