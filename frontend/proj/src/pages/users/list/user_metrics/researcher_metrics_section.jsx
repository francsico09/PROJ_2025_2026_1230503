import { Fragment } from 'react';
import Badge from '../../../../components/badge.jsx';
import Icon, { ICONS } from '../../../../components/icon.jsx';
import ConfirmDialog from '../../../../components/confirm_dialog.jsx';

export default function ResearcherMetricsSection({
                                                     expandedMetrics,
                                                     metrics,
                                                     total,
                                                     page,
                                                     pages,
                                                     onPageChange,
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
                    {/* ── Header ── */}
                    <div style={{ marginBottom: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <h4 style={{ margin: 0, fontSize: 13, color: 'var(--text-2)' }}>
                            {metricsLoading ? '—' : `${total ?? metrics?.length ?? 0} metrics`}
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

                    {/* ── Loading ── */}
                    {metricsLoading && (
                        <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-3)', fontSize: 13 }}>
                            Loading metrics…
                        </div>
                    )}

                    {/* ── Error ── */}
                    {!metricsLoading && metricsError && (
                        <div className="alert alert-danger" style={{ marginBottom: '12px' }}>
                            {metricsError}
                        </div>
                    )}

                    {/* ── Empty ── */}
                    {!metricsLoading && metrics?.length === 0 && (
                        <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-3)', fontSize: 13 }}>
                            No metrics available
                        </div>
                    )}

                    {/* ── Table ── */}
                    {!metricsLoading && metrics?.length > 0 && (
                        <div style={{ borderRadius: '6px', border: '1px solid var(--border)', overflow: 'hidden', width: '100%' }}>
                            <table style={{ width: '100%', marginBottom: 0 }}>
                                <thead>
                                <tr style={{ backgroundColor: 'var(--surface-2)' }}>
                                    <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: '11px' }}>h-index</th>
                                    <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: '11px' }}>i10</th>
                                    <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: '11px' }}>Citations</th>
                                    <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: '11px' }}>Publications</th>
                                    <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: '11px' }}>Source</th>
                                    <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: '11px' }}>Date</th>
                                    <th style={{ padding: '8px 12px', textAlign: 'right' }}></th>
                                </tr>
                                </thead>
                                <tbody>
                                {metrics.map(metric => (
                                    <Fragment key={metric.id}>
                                        <tr
                                            onClick={() => onRowClick(metric)}
                                            style={{
                                                backgroundColor: selectedMetricId === metric.id ? 'var(--accent-light)' : 'transparent',
                                                cursor: 'pointer',
                                                borderBottom: '1px solid var(--border)',
                                            }}
                                        >
                                            <td style={{ padding: '8px 12px', fontSize: '13px', fontWeight: 600 }}>
                                                {metric.h_index}
                                            </td>
                                            <td style={{ padding: '8px 12px', fontSize: '13px' }}>
                                                {metric.i10_index ?? '—'}
                                            </td>
                                            <td style={{ padding: '8px 12px', fontSize: '13px' }}>
                                                {metric.total_citations?.toLocaleString() ?? '—'}
                                            </td>
                                            <td style={{ padding: '8px 12px', fontSize: '13px' }}>
                                                {metric.total_publications ?? '—'}
                                            </td>
                                            <td style={{ padding: '8px 12px', fontSize: '13px' }}>
                                                <Badge variant={metric.source?.name ?? 'scholar'}>
                                                    {metric.source?.name ?? '—'}
                                                </Badge>
                                            </td>
                                            <td style={{ padding: '8px 12px', fontSize: '12px', color: 'var(--text-3)' }}>
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
                                            <tr style={{ backgroundColor: 'var(--surface-2)' }}>
                                                <td colSpan={7} style={{ padding: '10px 12px' }}>
                                                    <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                                                        <button
                                                            className="btn btn-primary"
                                                            onClick={(e) => { e.stopPropagation(); onEdit(metric); }}
                                                            style={{ padding: '5px 10px', fontSize: '12px' }}
                                                        >
                                                            <Icon d={ICONS.edit} size={12} />
                                                            Edit
                                                        </button>
                                                        <button
                                                            className="btn btn-danger"
                                                            onClick={(e) => { e.stopPropagation(); onDeleteClick(metric); }}
                                                            style={{ padding: '5px 10px', fontSize: '12px' }}
                                                        >
                                                            <Icon d={ICONS.trash} size={12} />
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

                            {/* ── Pagination ── */}
                            {pages > 1 && (
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'flex-end',
                                    gap: 6,
                                    padding: '8px 12px',
                                    borderTop: '1px solid var(--border)',
                                    background: 'var(--surface)',
                                }}>
                                    <button
                                        className="btn btn-outline"
                                        style={{ height: 28, padding: '0 10px', fontSize: 12 }}
                                        onClick={() => onPageChange(page - 1)}
                                        disabled={page === 1}
                                    >
                                        ←
                                    </button>
                                    <span style={{ fontSize: 12, color: 'var(--text-2)' }}>
                                        {page} / {pages}
                                    </span>
                                    <button
                                        className="btn btn-outline"
                                        style={{ height: 28, padding: '0 10px', fontSize: 12 }}
                                        onClick={() => onPageChange(page + 1)}
                                        disabled={page === pages}
                                    >
                                        →
                                    </button>
                                </div>
                            )}
                        </div>
                    )}

                    <ConfirmDialog
                        open={!!deleteTarget}
                        title="Delete metric?"
                        message="This will permanently delete this metric. This action cannot be undone."
                        confirmLabel={deleting ? 'Deleting…' : 'Delete metric'}
                        onConfirm={onDeleteConfirm}
                        onCancel={onDeleteCancel}
                    />
                </div>
            )}
        </>
    );
}