/**
 * Component to display average metrics for an organization, such as average
 * h-index, i10-index, citations, and publications.
 * It accepts an 'averages' object containing the metrics and an optional
 * 'source' string to indicate the data source.
 *
 * @param averages
 * @param source
 * @returns {React.JSX.Element|null}
 * @constructor
 */

export default function OrgAveragesCard({ averages, source }) {
    if (!averages)
        return null;

    const stats = [
        { label: 'Avg. h-index', value: averages.h_index, hint: null },
        { label: 'Avg. i10-index', value: averages.i10_index, hint: null },
        { label: 'Avg. citations', value: averages.total_citations?.toLocaleString(), hint: null },
        { label: 'Avg. publications', value: averages.total_publications, hint: null },
        { label: 'Avg. h-index (5y)', value: averages.h_index_5y ?? '—', hint: 'Scholar only' },
        { label: 'Avg. citations (5y)', value: averages.citations_5y?.toLocaleString() ?? '—', hint: 'Scholar only' },
    ];

    return (
        <div className="org-averages-grid">
            {stats.map(stat => (
                <div key={stat.label} className="org-stat-card">
                    <div className="org-stat-label">
                        {stat.label}
                        {stat.hint && <span className="org-stat-hint"> · {stat.hint}</span>}
                    </div>
                    <div className="org-stat-value">{stat.value ?? '—'}</div>
                    {source && (
                        <div className="org-stat-source">{source}</div>
                    )}
                </div>
            ))}
        </div>
    );
}