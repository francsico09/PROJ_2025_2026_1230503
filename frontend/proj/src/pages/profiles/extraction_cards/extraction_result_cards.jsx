import { useState } from 'react';
import Badge from '../../../components/badge.jsx';
import Icon, { ICONS } from '../../../components/icon.jsx';

export default function ExtractionResultCards({ metrics, onClose }) {
    const [index, setIndex] = useState(0);

    if (!metrics?.length) return null;

    const metric  = metrics[index];
    const isFirst = index === 0;
    const isLast  = index === metrics.length - 1;

    const fields = [
        { label: 'h-index',            value: metric.h_index },
        { label: 'i10-index',          value: metric.i10_index          ?? '—' },
        { label: 'Total citations',    value: metric.total_citations?.toLocaleString() },
        { label: 'Total publications', value: metric.total_publications },
        { label: 'h-index (5y)',       value: metric.h_index_5y         ?? '—' },
        { label: 'i10-index (5y)',     value: metric.i10_index_5y       ?? '—' },
        { label: 'Citations (5y)',     value: metric.citations_5y?.toLocaleString() ?? '—' },
    ];

    return (
        <div className="extraction-result-overlay">
            <div className="extraction-result-card">

                {/* ── Header ── */}
                <div className="extraction-result-header">
                    <div>
                        <div className="extraction-result-title">Extraction complete</div>
                        <div className="extraction-result-subtitle">
                            {metrics.length} metric{metrics.length > 1 ? 's' : ''} extracted
                        </div>
                    </div>
                    <button className="btn btn-ghost" onClick={onClose}>
                        <Icon d={ICONS.close} size={15} />
                    </button>
                </div>

                {/* ── Source + date ── */}
                <div className="extraction-result-meta">
                    <Badge variant={metric.source?.name ?? 'scholar'}>
                        {metric.source?.name ?? '—'}
                    </Badge>
                    <span className="text-hint">
                        {metric.date ? new Date(metric.date).toLocaleDateString() : '—'}
                    </span>
                </div>

                {/* ── Metric fields ── */}
                <div className="extraction-result-fields">
                    {fields.map(f => (
                        <div key={f.label} className="extraction-result-field">
                            <span className="extraction-result-field-label">{f.label}</span>
                            <span className="extraction-result-field-value">{f.value}</span>
                        </div>
                    ))}
                </div>

                {/* ── Navigation ── */}
                {metrics.length > 1 && (
                    <div className="extraction-result-nav">
                        <button
                            className="btn btn-outline"
                            onClick={() => setIndex(i => i - 1)}
                            disabled={isFirst}
                        >
                            ← Previous
                        </button>
                        <span className="text-hint">
                            {index + 1} / {metrics.length}
                        </span>
                        <button
                            className="btn btn-outline"
                            onClick={() => setIndex(i => i + 1)}
                            disabled={isLast}
                        >
                            Next →
                        </button>
                    </div>
                )}

                {/* ── Close ── */}
                <button
                    className="btn btn-primary"
                    style={{ width: '100%', marginTop: 8 }}
                    onClick={onClose}
                >
                    Done
                </button>
            </div>
        </div>
    );
}