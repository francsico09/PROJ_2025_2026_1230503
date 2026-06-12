import OrgResearchersTable from "./components/aggregated_researcher_table.jsx";
import OrgAveragesCard from "./components/aggregated_average_card.jsx";
import SourceSelector from "../individual/components/source_selector.jsx";

export default function AggregatedDashboardView({
                                                    users,
                                                    latestByResearcher,
                                                    averages,
                                                    availableSources,
                                                    selectedSource,
                                                    onSourceChange,
                                                    selectedMetric,
                                                    onMetricChange,
                                                    loadingMetrics,
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
                <div className="dashboard-source-selector" style={{ marginBottom: 20 }}>
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
                        <div style={{ color: 'var(--text-3)', fontSize: 14 }}>Loading…</div>
                    ) : (
                        <OrgAveragesCard averages={averages} source={selectedSource} />
                    )}
                </div>
            </div>

            <OrgResearchersTable
                users={users}
                latestByResearcher={latestByResearcher}
                loading={loadingMetrics}
                selectedMetric={selectedMetric}
                onMetricChange={onMetricChange}
            />
        </div>
    );
}