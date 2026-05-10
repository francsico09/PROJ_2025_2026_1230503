import Icon, { ICONS } from '../../../components/icon.jsx';

export default function MetricCreateView({
                                             form,
                                             researchers,
                                             loadingUsers,
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
                <Icon d={ICONS.back} size={13} />
                Back to metrics
            </button>

            <div className="page-header">
                <h2>Create metric</h2>
                <p>Manually add a new metric record for a researcher.</p>
            </div>

            <form className="edit-card" onSubmit={onSubmit}>
                <div className="edit-card-title">Researcher</div>

                <div className="form-group">
                    <label>Researcher</label>
                    <select
                        className="form-select"
                        value={form.researcher_id}
                        onChange={e => onChange('researcher_id', e.target.value)}
                        required
                        disabled={loadingUsers}
                    >
                        <option value="">
                            {loadingUsers ? 'Loading…' : '— Select a researcher —'}
                        </option>
                        {researchers.map(u => (
                            <option key={u.id} value={u.id}>{u.name}</option>
                        ))}
                    </select>
                </div>

                <div className="edit-card-title" style={{ marginTop: 8 }}>
                    Metric values
                </div>

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

                <div className="edit-card-title" style={{ marginTop: 8 }}>
                    Source
                </div>

                <div className="form-row">
                    <div className="form-group">
                        <label>Source</label>
                        <select
                            className="form-select"
                            value={form.source_name}
                            onChange={e => onChange('source_name', e.target.value)}
                            required
                        >
                            <option value="scholar">scholar</option>
                            <option value="orcid">orcid</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label>
                            Source URL <span className="hint">(optional)</span>
                        </label>
                        <input
                            className="form-input"
                            type="url"
                            value={form.source_url}
                            onChange={e => onChange('source_url', e.target.value)}
                        />
                    </div>
                </div>

                {success && (
                    <div className="alert alert-success">
                        <Icon d={ICONS.check} size={14} />
                        Metric created successfully.
                    </div>
                )}

                {error && (
                    <div className="alert alert-danger">{error}</div>
                )}

                <div className="form-actions">
                    <button type="submit" className="btn btn-primary" disabled={saving}>
                        {saving && <span className="spinner" />}
                        {saving ? 'Creating…' : 'Create metric'}
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