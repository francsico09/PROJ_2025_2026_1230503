import { useResearcherMetrics } from '../../../../hooks/use_researcher_metrics.js';
import { useDeleteConfirm } from '../../../../hooks/use_delete_confirm.js';
import ResearcherMetricsSection from './researcher_metrics_section.jsx';
import {useState} from "react";

export default function ResearcherMetricsUserRow({
    user,
    expandedMetricsId,
    onExpandMetrics,
    onEditMetric,
    onCreateMetric,
    showOnlyTable = false,
}) {
    const [selectedMetricId, setSelectedMetricId] = useState(null);

    const { metrics, loading, error, remove } = useResearcherMetrics(user.id);

    const isExpanded = expandedMetricsId === user.id;

    const handleEditMetric = (metric) => {
        onEditMetric?.(metric, user);
    };

    const handleCreateMetric = () => {
        onCreateMetric?.(user);
    };

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
                metricsLoading={loading}
                metricsError={error}
                selectedMetricId={selectedMetricId}
                deleteTarget={deleteTarget}
                deleting={deleting}
                onToggleExpand={() => onExpandMetrics(user.id)}
                onRowClick={(metric) => setSelectedMetricId(metric.id)}
                onEdit={handleEditMetric}
                onCreate={handleCreateMetric}
                onDeleteClick={handleDeleteClick}
                onDeleteConfirm={handleDeleteConfirm}
                onDeleteCancel={handleDeleteCancel}
                showOnlyTable={showOnlyTable}
            />
        </div>
    );
}
