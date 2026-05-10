export default function OrgResearchersTable({ users, latestByResearcher, loading }) {
    const metricByResearcherId = Object.fromEntries(
        latestByResearcher.map(m => [m.researcher_id, m])
    );

    if (loading) {
        return (
            <div className="card">
                <div className="loading-row" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-3)' }}>
                    Loading researchers…
                </div>
            </div>
        );
    }

    return (
        <div className="card">
            <div className="card-header">
                <h3>{users?.length ?? 0} researchers</h3>
            </div>
            <table>
                <thead>
                <tr>
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
                {!users?.length && (
                    <tr className="loading-row">
                        <td colSpan={8}>No researchers found.</td>
                    </tr>
                )}
                {users?.map(user => {
                    const profileId = user.researcherProfile?.id ?? user.researcher_profile_id;
                    const metric    = profileId ? metricByResearcherId[profileId] : null;

                    return (
                        <tr key={user.id}>
                            <td>
                                <div className="user-cell">
                                    <div className="user-cell-avatar">
                                        {user.name?.slice(0, 2).toUpperCase()}
                                    </div>
                                    <div>
                                        <div className="user-cell-name">{user.name}</div>
                                        <div style={{ fontSize: 11.5, color: 'var(--text-3)' }}>{user.email}</div>
                                    </div>
                                </div>
                            </td>
                            <td>{metric ? <strong>{metric.h_index}</strong> : <span className="text-hint">—</span>}</td>
                            <td>{metric?.i10_index ?? <span className="text-hint">—</span>}</td>
                            <td>{metric ? metric.total_citations?.toLocaleString() : <span className="text-hint">—</span>}</td>
                            <td>{metric?.total_publications ?? <span className="text-hint">—</span>}</td>
                            <td>{metric?.h_index_5y ?? <span className="text-hint">—</span>}</td>
                            <td>{metric?.citations_5y?.toLocaleString() ?? <span className="text-hint">—</span>}</td>
                            <td className="text-muted" style={{ fontSize: 12 }}>
                                {metric?.date
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