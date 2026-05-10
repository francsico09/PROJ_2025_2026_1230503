import SourceSelector from "../individual/components/source_selector.jsx";
import OrgAveragesCard from "./components/aggregated_average_card.jsx";
import OrgResearchersTable from "./components/aggregated_researcher_table.jsx";

export default function AggregatedDashboardView({
                                                    researchers,
                                                    latestByResearcher,
                                                    averages,
                                                    availableSources,
                                                    selectedSource,
                                                    onSourceChange,
                                                    loadingMetrics,
                                                    loadingUsers,
                                                    error,
                                                }) {
    return (
        <div>
            <div className="page-header">
                <h2>Organisation Dashboard</h2>
                <p>Aggregated research metrics across all active researchers.</p>
            </div>

            {error && (
                <div className="alert alert-danger" style={{ marginBottom: 20 }}>
                    {error}
                </div>
            )}

            {/* ── Source selector ── */}
            {availableSources.length > 0 && (
                <div
                    className="dashboard-source-selector"
                    style={{ marginBottom: 20 }}
                >
                    <SourceSelector
                        availableSources={availableSources}
                        selectedSource={selectedSource}
                        onSourceChange={onSourceChange}
                    />
                </div>
            )}

            {/* ── Averages ── */}
            <div className="card" style={{ marginBottom: 24 }}>
                <div className="card-header">
                    <h3>Organisation averages</h3>

                    <span className="card-header-subtitle">
                        Based on most recent metric per researcher
                        {selectedSource && ` · ${selectedSource}`}
                    </span>
                </div>

                <div style={{ padding: '20px' }}>
                    {loadingMetrics ? (
                        <div
                            style={{
                                color: 'var(--text-3)',
                                fontSize: 14
                            }}
                        >
                            Loading…
                        </div>
                    ) : (
                        <OrgAveragesCard
                            averages={averages}
                            source={selectedSource}
                        />
                    )}
                </div>
            </div>

            {/* ── Researchers table ── */}
            <OrgResearchersTable
                users={researchers}
                latestByResearcher={latestByResearcher}
                loading={loadingMetrics || loadingUsers}
            />
        </div>
    );
}