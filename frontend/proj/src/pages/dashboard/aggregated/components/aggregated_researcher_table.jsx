import {useMemo} from "react";

export default function OrgResearchersTable({ users, latestByResearcher, loading, selectedMetric, onMetricChange }) {
    const metricOptions = [
        { value: 'h_index', label: 'h-index' },
        { value: 'i10_index', label: 'i10-index' },
        { value: 'total_citations', label: 'Total Citations' },
        { value: 'total_publications', label: 'Total Publications' },
        { value: 'h_index_5y', label: 'h-index (5y)' },
        { value: 'citations_5y', label: 'Citations (5y)' },
    ];

    const userByProfileId = useMemo(() => {
        const map = {};

        users.forEach(u => {
            if (u.researcherProfile && u.researcherProfile.id) {
                map[u.researcherProfile.id] = u;
            }
        });
        return map;
    }, [users]);

    if (loading) {
        return (
            <div className="card">
                <div className="loading-row" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-3)' }}>
                    Loading Top 10 ranking…
                </div>
            </div>
        );
    }

    return (
        <div className="card">
            <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                <div>
                    <h3>Top 10 Researchers</h3>
                    <p style={{ fontSize: 12.5, color: 'var(--text-3)', margin: 0 }}>
                        Based on the best metrics retrieved from the backend
                    </p>
                </div>

                <div className="metric-filter-container" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <label style={{ fontSize: 13.5, color: 'var(--text-2)' }}>Rank by:</label>
                    <select
                        className="form-input"
                        style={{ width: 'auto', padding: '6px 12px', height: 'auto' }}
                        value={selectedMetric}
                        onChange={(e) => onMetricChange(e.target.value)}
                    >
                        {metricOptions.map(opt => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                    </select>
                </div>
            </div>

            <table>
                <thead>
                <tr>
                    <th style={{ width: '50px', textAlign: 'center' }}>Rank</th>
                    <th>Researcher</th>
                    <th>h-index</th>
                    <th>i10-index</th>
                    <th>Citations</th>
                    <th>Publications</th>
                    <th>h-index (5y)</th>
                    <th>Citations (5y)</th>
                    <th>Last updated</th>
                </tr>
                </thead>
                <tbody>
                {!latestByResearcher?.length && (
                    <tr className="loading-row">
                        <td colSpan={9}>No researchers found.</td>
                    </tr>
                )}

                {latestByResearcher?.map((metric, index) => {
                    const user = userByProfileId[metric.researcher_id];

                    return (
                        <tr key={metric.researcher_id || index}>
                            <td style={{ textAlign: 'center', fontWeight: 'bold', color: index < 3 ? 'var(--primary)' : 'var(--text-3)' }}>
                                #{index + 1}
                            </td>

                            <td>
                                <div className="user-cell">
                                    <div className="user-cell-avatar">
                                        {(user?.name || 'UN').slice(0, 2).toUpperCase()}
                                    </div>
                                    <div>
                                        <div className="user-cell-name">{user?.name || 'Unknown Researcher'}</div>
                                        <div style={{ fontSize: 11.5, color: 'var(--text-3)' }}>{user?.email || 'No email synced'}</div>
                                    </div>
                                </div>
                            </td>

                            <td>{metric.h_index !== undefined ? <strong>{metric.h_index}</strong> : <span className="text-hint">—</span>}</td>
                            <td>{metric.i10_index ?? <span className="text-hint">—</span>}</td>
                            <td>{metric.total_citations !== undefined ? metric.total_citations?.toLocaleString() : <span className="text-hint">—</span>}</td>
                            <td>{metric.total_publications ?? <span className="text-hint">—</span>}</td>
                            <td>{metric.h_index_5y ?? <span className="text-hint">—</span>}</td>
                            <td>{metric.citations_5y?.toLocaleString() ?? <span className="text-hint">—</span>}</td>
                            <td className="text-muted" style={{ fontSize: 12 }}>
                                {metric.date
                                    ? new Date(metric.date).toLocaleDateString()
                                    : <span className="text-hint">No data</span>}
                            </td>
                        </tr>
                    );
                })}
                </tbody>
            </table>
        </div>
    );
}