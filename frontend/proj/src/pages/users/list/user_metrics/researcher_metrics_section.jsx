import { Fragment } from 'react';
import Badge from '../../../../components/badge.jsx';
import Icon, { ICONS } from '../../../../components/icon.jsx';
import ConfirmDialog from '../../../../components/confirm_dialog.jsx';

export default function ResearcherMetricsSection({
    expandedMetrics,
    metrics,
    metricsLoading,
    metricsError,
    selectedMetricId,
    deleteTarget,
    deleting,
    onToggleExpand,
    onRowClick,
    onEdit,
    onCreate,
    onDeleteClick,
    onDeleteConfirm,
    onDeleteCancel,
    showOnlyTable = false,
}) {
    return (
        <>
            {!showOnlyTable && (
                <button
                    className="btn btn-primary"
                    onClick={onToggleExpand}
                    style={{ width: '100%', marginBottom: expandedMetrics ? '12px' : '0' }}
                >
                    <Icon d={expandedMetrics ? ICONS.chevronD : ICONS.chevronR} size={13} />
                    {expandedMetrics ? 'Hide' : 'View'} metrics
                </button>
            )}

            {expandedMetrics && (
                <div style={{ width: '100%' }}>
                    <div style={{ marginBottom: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <h4 style={{ margin: 0 }}>
                            {metricsLoading ? '—' : `${metrics?.length || 0} metrics`}
                        </h4>
                        <button
                            className="btn btn-primary"
                            onClick={onCreate}
                            style={{ padding: '6px 12px', fontSize: '12px' }}
                        >
                            <Icon d={ICONS.plus} size={12} />
                            New metric
                        </button>
                    </div>

                    {metricsLoading && (
                        <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-3)' }}>
                            Loading metrics…
                        </div>
                    )}

                    {!metricsLoading && metricsError && (
                        <div className="alert alert-danger" style={{ marginBottom: '12px' }}>
                            {metricsError}
                        </div>
                    )}

                    {!metricsLoading && metrics?.length === 0 && (
                        <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-3)' }}>
                            No metrics available
                        </div>
                    )}

                    {!metricsLoading && metrics?.length > 0 && (
                        <div style={{ borderRadius: '6px', border: '1px solid var(--border)', overflow: 'hidden', width: '100%' }}>
                            <table style={{ width: '100%', marginBottom: 0 }}>
                                <thead>
                                <tr style={{ backgroundColor: 'var(--bg-2)' }}>
                                    <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: '12px' }}>h-index</th>
                                    <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: '12px' }}>i10-index</th>
                                    <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: '12px' }}>Citations</th>
                                    <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: '12px' }}>Publications</th>
                                    <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: '12px' }}>Source</th>
                                    <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: '12px' }}>Date</th>
                                    <th style={{ padding: '8px 12px', textAlign: 'right' }}></th>
                                </tr>
                                </thead>
                                <tbody>
                                {metrics.map(metric => (

                                    <Fragment key={metric.id}>
                                        <tr
                                            onClick={() => onRowClick(metric)}
                                            style={{
                                                backgroundColor: selectedMetricId === metric.id ? 'var(--bg-2)' : 'transparent',
                                                cursor: 'pointer',
                                            }}
                                        >
                                            <td style={{ padding: '8px 12px', fontSize: '13px', fontWeight: 600 }}>
                                                {metric.h_index}
                                            </td>
                                            <td style={{ padding: '8px 12px', fontSize: '13px' }}>
                                                {metric.i10_index}
                                            </td>
                                            <td style={{ padding: '8px 12px', fontSize: '13px' }}>
                                                {metric.total_citations?.toLocaleString()}
                                            </td>
                                            <td style={{ padding: '8px 12px', fontSize: '13px' }}>
                                                {metric.total_publications}
                                            </td>
                                            <td style={{ padding: '8px 12px', fontSize: '13px' }}>
                                                <Badge variant={metric.source?.name ?? 'scholar'}>
                                                    {metric.source?.name ?? '—'}
                                                </Badge>
                                            </td>
                                            <td style={{ padding: '8px 12px', fontSize: '13px', color: 'var(--text-3)' }}>
                                                {metric.date ? new Date(metric.date).toLocaleDateString() : '—'}
                                            </td>
                                            <td style={{ padding: '8px 12px', textAlign: 'right' }}>
                                                <Icon
                                                    d={ICONS.chevronR}
                                                    size={12}
                                                    style={{
                                                        color: 'var(--text-3)',
                                                        transform: selectedMetricId === metric.id ? 'rotate(90deg)' : 'none',
                                                        transition: 'transform 0.15s',
                                                    }}
                                                />
                                            </td>
                                        </tr>

                                        {selectedMetricId === metric.id && (
                                            <tr>
                                                <td colSpan={7} style={{ padding: '12px' }}>
                                                    <div style={{
                                                        display: 'flex',
                                                        gap: '8px',
                                                        justifyContent: 'flex-end',
                                                    }}>
                                                        <button
                                                            className="btn btn-primary"
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                onEdit(metric);
                                                            }}
                                                            style={{ padding: '6px 12px', fontSize: '12px' }}
                                                        >
                                                            <Icon d={ICONS.edit} size={13} />
                                                            Edit
                                                        </button>

                                                        <button
                                                            className="btn btn-danger"
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                onDeleteClick(metric);
                                                            }}
                                                            style={{ padding: '6px 12px', fontSize: '12px' }}
                                                        >
                                                            <Icon d={ICONS.trash} size={13} />
                                                            Delete
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        )}
                                    </Fragment>
                                ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    <ConfirmDialog
                        open={!!deleteTarget}
                        title="Delete metric?"
                        message={`This will permanently delete this metric. This action cannot be undone.`}
                        confirmLabel={deleting ? 'Deleting…' : 'Delete metric'}
                        onConfirm={onDeleteConfirm}
                        onCancel={onDeleteCancel}
                    />
                </div>
            )}
        </>
    );
}

