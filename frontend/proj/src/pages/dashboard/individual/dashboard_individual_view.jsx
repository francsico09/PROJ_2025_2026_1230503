import SourceSelector from './components/source_selector.jsx';
import CitationsBarChart from './components/citations_bar_chart.jsx';
import CitationsSummary from './components/citations_summary.jsx';
import IndexMetrics from './components/index_metrics.jsx';
import UserSelector from './components/user_selector.jsx';
import MetricsTimeline from "./components/metrics_timeline.jsx";

/**
 * IndividualDashboardView component is responsible for rendering the dashboard view
 * for an individual researcher.
 * It displays the researcher's metrics, allows source selection, and shows relevant charts
 * and summaries. Admin users can select any researcher to view their dashboard, while regular
 * users see their own metrics.
 *
 * @param isAdmin
 * @param selectedUserId
 * @param setSelectedUserId
 * @param allMetrics
 * @param currentMetric
 * @param loading
 * @param error
 * @param selectedSource
 * @param setSelectedSource
 * @param availableSources
 * @returns {React.JSX.Element}
 * @constructor
 */
export default function IndividualDashboardView({
                                                    isAdmin,
                                                    selectedUserId,
                                                    setSelectedUserId,
                                                    allMetrics,
                                                    currentMetric,
                                                    loading,
                                                    error,
                                                    selectedSource,
                                                    setSelectedSource,
                                                    availableSources,
                                                }) {
    return (
        <div>
            <div className="page-header">
                <h2>Dashboard</h2>
                <p>
                    {isAdmin
                        ? 'View research researcher_metric for any researcher in the system.'
                        : 'Your research researcher_metric overview and analytics.'
                    }
                </p>
            </div>

            {isAdmin && (
                <div className="card admin-card-padding">
                    <UserSelector
                        selectedUserId={selectedUserId}
                        onUserSelect={setSelectedUserId}
                    />
                </div>
            )}

            {isAdmin && !selectedUserId && (
                <div className="card">
                    <div className="empty-state">
                        <div className="empty-icon">👤</div>
                        <span>Select a researcher to view their dashboard</span>
                        <p className="empty-state-text">
                            Choose a researcher from the dropdown above to see their metrics.
                        </p>
                    </div>
                </div>
            )}

            {(!isAdmin || selectedUserId) && (
                <>
                    {loading && (
                        <div className="card">
                            <div className="dashboard-loading">
                                <div>
                                    Loading {isAdmin ? 'researcher' : 'your'} metrics…
                                </div>
                            </div>
                        </div>
                    )}

                    {error && !loading && (
                        <div className="alert alert-danger dashboard-source-selector">
                            {error}
                        </div>
                    )}

                    {!loading && !error && allMetrics.length === 0 && (
                        <div className="card">
                            <div className="empty-state">
                                <div className="empty-icon">◎</div>
                                <span>No metrics available yet</span>
                                <p className="empty-state-text">
                                    {isAdmin
                                        ? 'This researcher has no researcher_metric available yet.'
                                        : 'Your researcher_metric will appear here once they have been extracted.'
                                    }
                                </p>
                            </div>
                        </div>
                    )}

                    {!loading && !error && allMetrics.length > 0 && (
                        <>
                            {availableSources.length > 0 && (
                                <div className="dashboard-source-selector">
                                    <SourceSelector
                                        availableSources={availableSources}
                                        selectedSource={selectedSource}
                                        onSourceChange={setSelectedSource}
                                    />
                                </div>
                            )}

                            {currentMetric && (
                                <div className="card">
                                    <div className="card-header">
                                        <h3>Index Metrics</h3>
                                        <span className="card-header-subtitle">
                                            {currentMetric.date &&
                                                `as of ${new Date(currentMetric.date).toLocaleDateString()}`}
                                        </span>
                                    </div>
                                    <div className="admin-card-padding">
                                        <IndexMetrics metric={currentMetric} />
                                    </div>
                                </div>
                            )}

                            {currentMetric && (
                                <div className="card">
                                    <div className="card-header">
                                        <h3>Citations Over Time</h3>
                                        <span className="card-header-subtitle">
                                            {selectedSource ? `${selectedSource} source` : 'All sources'}
                                        </span>
                                    </div>
                                    <div className="admin-card-padding">
                                        <div className="dashboard-chart-container">
                                            <CitationsBarChart
                                                metric={currentMetric}
                                            />
                                        </div>

                                        <CitationsSummary metric={currentMetric} />
                                    </div>
                                </div>
                            )}

                            {allMetrics.length > 0 && (
                                <MetricsTimeline
                                    allMetrics={allMetrics}
                                    selectedSource={selectedSource}
                                />
                            )}
                        </>
                    )}
                </>
            )}
        </div>
    );
}