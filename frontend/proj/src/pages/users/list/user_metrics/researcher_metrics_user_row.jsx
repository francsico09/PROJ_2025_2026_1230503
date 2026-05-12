import { useResearcherMetrics } from '../../../../hooks/use_researcher_metrics.js';
import { useDeleteConfirm } from '../../../../hooks/use_delete_confirm.js';
import ResearcherMetricsSection from './researcher_metrics_section.jsx';
import { useState } from 'react';

export default function ResearcherMetricsUserRow({
                                                     user,
                                                     expandedMetricsId,
                                                     onExpandMetrics,
                                                     onEditMetric,
                                                     onCreateMetric,
                                                     showOnlyTable = false,
                                                 }) {
    const [selectedMetricId, setSelectedMetricId] = useState(null);

    const {
        items: metrics,
        total,
        page,
        pages,
        setPage,
        loading,
        error,
        remove,
    } = useResearcherMetrics(user.id, { initialPageSize: 5 });

    const isExpanded = expandedMetricsId === user.id;

    const {
        deleteTarget,
        deleting,
        handleDeleteClick,
        handleDeleteConfirm,
        handleDeleteCancel,
    } = useDeleteConfirm(remove, () => setSelectedMetricId(null));

    return (
        <div style={{ width: '100%' }}>
            <ResearcherMetricsSection
                expandedMetrics={showOnlyTable || isExpanded}
                metrics={metrics}
                total={total}
                page={page}
                pages={pages}
                onPageChange={setPage}
                metricsLoading={loading}
                metricsError={error}
                selectedMetricId={selectedMetricId}
                deleteTarget={deleteTarget}
                deleting={deleting}
                onToggleExpand={() => onExpandMetrics(user.id)}
                onRowClick={(metric) => setSelectedMetricId(metric.id)}
                onEdit={(metric) => onEditMetric?.(metric, user)}
                onCreate={() => onCreateMetric?.(user)}
                onDeleteClick={handleDeleteClick}
                onDeleteConfirm={handleDeleteConfirm}
                onDeleteCancel={handleDeleteCancel}
                showOnlyTable={showOnlyTable}
            />
        </div>
    );
}