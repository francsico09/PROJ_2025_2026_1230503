import Icon, {ICONS} from '../../../components/icon.jsx';
import Badge from '../../../components/badge.jsx';

export default function MetricEditView({
                                           item,
                                           form,
                                           saving,
                                           success,
                                           error,
                                           onBack,
                                           onChange,
                                           onSubmit
                                       }) {
    return (
        <div>
            <button className="back-btn" onClick={onBack}>
                <Icon d={ICONS.back} size={13}/>
                Back to metrics
            </button>

            <div className="page-header">
                <h2>Edit metric</h2>
                <p>
                    {item.researcher_name ?? item.researcher_id}
                    {' · '}
                    <Badge variant={item.source?.name ?? 'scholar'}>
                        {item.source?.name ?? '—'}
                    </Badge>
                    {item.date && ` · ${new Date(item.date).toLocaleDateString()}`}
                </p>
            </div>

            <form className="edit-card" onSubmit={onSubmit}>
                <div className="edit-card-title">Metric values</div>

                <div className="form-row">
                    <div className="form-group">
                        <label>h-index</label>
                        <input
                            className="form-input"
                            type="number"
                            min={0}
                            value={form.h_index}
                            onChange={e => onChange('h_index', e.target.value)}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label>i10-index</label>
                        <input
                            className="form-input"
                            type="number"
                            min={0}
                            value={form.i10_index}
                            onChange={e => onChange('i10_index', e.target.value)}
                            required
                        />
                    </div>
                </div>

                <div className="form-row">
                    <div className="form-group">
                        <label>Total citations</label>
                        <input
                            className="form-input"
                            type="number"
                            min={0}
                            value={form.total_citations}
                            onChange={e => onChange('total_citations', e.target.value)}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label>Total publications</label>
                        <input
                            className="form-input"
                            type="number"
                            min={0}
                            value={form.total_publications}
                            onChange={e => onChange('total_publications', e.target.value)}
                            required
                        />
                    </div>
                </div>

                {/* Read-only info */}
                <div className="metric-readonly-fields">
                    <div className="user-dropdown-field">
                        <span className="detail-label">Source</span>
                        <Badge variant={item.source?.name ?? 'scholar'}>
                            {item.source?.name ?? '—'}
                        </Badge>
                    </div>

                    <div className="user-dropdown-field">
                        <span className="detail-label">Collection date</span>
                        <span className="text-muted" style={{fontSize: 13}}>
                            {item.date ? new Date(item.date).toLocaleDateString() : '—'}
                        </span>
                    </div>

                    {item.source?.url && (
                        <div className="user-dropdown-field">
                            <span className="detail-label">Source URL</span>
                            <a
                                href={item.source.url}
                                target="_blank"
                                rel="noreferrer"
                                className="text-muted"
                                style={{fontSize: 12}}
                            >
                                {item.source.url}
                            </a>
                        </div>
                    )}
                </div>

                {success && (
                    <div className="alert alert-success">
                        <Icon d={ICONS.check} size={14}/>
                        Changes saved successfully.
                    </div>
                )}

                {error && (
                    <div className="alert alert-danger">{error}</div>
                )}

                <div className="form-actions">
                    <button type="submit" className="btn btn-primary" disabled={saving}>
                        {saving && <span className="spinner"/>}
                        {saving ? 'Saving…' : 'Save changes'}
                    </button>

                    <button
                        type="button"
                        className="btn btn-outline"
                        onClick={onBack}
                        disabled={saving}
                    >
                        Cancel
                    </button>
                </div>
            </form>
        </div>
    );
}