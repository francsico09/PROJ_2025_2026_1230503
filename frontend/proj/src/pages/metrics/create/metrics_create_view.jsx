import Icon, { ICONS } from '../../../components/icon.jsx';

export default function MetricCreateView({
                                             form,
                                             researchers,
                                             saving,
                                             success,
                                             error,
                                             onBack,
                                             onChange,
                                             onSubmit
                                         }) {
    // Get the selected researcher's name
    const selectedResearcher = researchers.find(r => r.id === form.researcher_id);
    
    return (
        <div>
            <button className="back-btn" onClick={onBack}>
                <Icon d={ICONS.back} size={13} />
                Back to metrics
            </button>

            <div className="page-header">
                <h2>Create metric</h2>
                <p>
                    {selectedResearcher ? selectedResearcher.name : 'Manually add a new metric record for a researcher.'}
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
                        <label>h-index 5y</label>
                        <input
                            className="form-input"
                            type="number"
                            min={0}
                            value={form.h_index_5y}
                            onChange={e => onChange('h_index_5y', e.target.value)}
                            optional
                        />
                    </div>
                </div>

                <div className="form-row">
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

                    <div className="form-group">
                        <label>i10-index 5y</label>
                        <input
                            className="form-input"
                            type="number"
                            min={0}
                            value={form.i10_index_5y}
                            onChange={e => onChange('i10_index_5y', e.target.value)}
                            optional
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

                <div className="form-group">
                    <label>Citations 5y</label>
                    <input
                        className="form-input"
                        type="number"
                        min={0}
                        value={form.citations_5y}
                        onChange={e => onChange('citations_5y', e.target.value)}
                        optional
                    />
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
                            <option value="scholar">Google Scholar</option>
                            <option value="orcid">ORCID</option>
                            <option value="web_of_science">Web Of Science</option>
                            <option value="scopus">Scopus</option>
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