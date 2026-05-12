/**
 * A card component to display a single metric with an optional subtitle.
 *
 * @param label
 * @param value
 * @param subtitle
 * @param variant
 * @returns {React.JSX.Element}
 * @constructor
 */
export default function MetricCard({ label, value, subtitle, variant = 'default' }) {
    const isLoading = value === null || value === undefined;

    return (
        <div className={`metric-card ${variant !== 'default' ? variant : ''}`}>
            <div className="metric-card-label">
                {label}
            </div>
            <div className={`metric-card-value ${subtitle ? 'metric-card-value-with-subtitle' : ''}`}>
                {isLoading ? '—' : value.toLocaleString?.() || value}
            </div>
            {subtitle && (
                <div className="metric-card-subtitle">
                    {subtitle}
                </div>
            )}
        </div>
    );
}

