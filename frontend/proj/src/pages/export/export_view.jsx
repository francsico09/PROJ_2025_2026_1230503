import { FORMAT_OPTIONS, SCOPE_OPTIONS } from './constants.js';

import Icon, { ICONS } from '../../components/icon.jsx';
import Badge from '../../components/badge.jsx';

/**
 * ExportView component renders the UI for configuring and initiating the export of
 * researcher metrics.
 *
 * @param isAdmin
 * @param format
 * @param setFormat
 * @param scope
 * @param setScope
 * @param startDate
 * @param setStartDate
 * @param endDate
 * @param setEndDate
 * @param searchQuery
 * @param setSearch
 * @param selectedUser
 * @param setSelected
 * @param exportAll
 * @param setExportAll
 * @param loading
 * @param success
 * @param error
 * @param loadingUsers
 * @param filtered
 * @param canExport
 * @param handleExport
 * @returns {React.JSX.Element}
 * @constructor
 */
export default function ExportView({
                                       isAdmin,
                                       format,
                                       setFormat,
                                       scope,
                                       setScope,
                                       startDate,
                                       setStartDate,
                                       endDate,
                                       setEndDate,
                                       searchQuery,
                                       setSearch,
                                       selectedUser,
                                       setSelected,
                                       exportAll,
                                       setExportAll,
                                       loading,
                                       success,
                                       error,
                                       loadingUsers,
                                       filtered,
                                       canExport,
                                       handleExport,
                                   }) {
    return (
        <div>
            <div className="page-header">
                <h2>Export metrics</h2>
                <p>Download researcher metrics as Excel or CSV.</p>
            </div>

            <div className="export-layout">

                {/* LEFT */}
                <div className="export-config">

                    {/* FORMAT */}
                    <div className="export-section">
                        <div className="export-section-title">Format</div>

                        <div className="export-option-group">
                            {FORMAT_OPTIONS.map(opt => (
                                <button
                                    key={opt.value}
                                    className={`export-option ${format === opt.value ? 'selected' : ''}`}
                                    onClick={() => setFormat(opt.value)}
                                    type="button"
                                >
                                    <span className="export-option-icon">
                                        {opt.icon}
                                    </span>

                                    <div>
                                        <div className="export-option-label">
                                            {opt.label}
                                        </div>

                                        <div className="export-option-desc">
                                            {opt.description}
                                        </div>
                                    </div>

                                    {format === opt.value && (
                                        <span className="export-option-check">
                                            <Icon d={ICONS.check} size={13} />
                                        </span>
                                    )}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* SCOPE */}
                    <div className="export-section">
                        <div className="export-section-title">Data range</div>

                        <div className="export-option-group">
                            {SCOPE_OPTIONS.map(opt => (
                                <button
                                    key={opt.value}
                                    className={`export-option ${scope === opt.value ? 'selected' : ''}`}
                                    onClick={() => setScope(opt.value)}
                                    type="button"
                                >
                                    <div>
                                        <div className="export-option-label">
                                            {opt.label}
                                        </div>

                                        <div className="export-option-desc">
                                            {opt.description}
                                        </div>
                                    </div>

                                    {scope === opt.value && (
                                        <span className="export-option-check">
                                            <Icon d={ICONS.check} size={13} />
                                        </span>
                                    )}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* CUSTOM DATE RANGE */}
                    {scope === 'custom' && (
                        <div className="export-section" style={{ backgroundColor: 'var(--bg-2)', padding: 12, borderRadius: 6 }}>
                            <div className="export-section-title">Date range</div>

                            <div style={{ display: 'flex', gap: 12 }}>
                                <div style={{ flex: 1 }}>
                                    <label style={{ display: 'block', fontSize: 12, fontWeight: 500, marginBottom: 6, color: 'var(--text-2)' }}>
                                        From
                                    </label>
                                    <input
                                        type="date"
                                        value={startDate}
                                        onChange={e => setStartDate(e.target.value)}
                                        className="form-input"
                                        style={{ width: '100%' }}
                                    />
                                </div>

                                <div style={{ flex: 1 }}>
                                    <label style={{ display: 'block', fontSize: 12, fontWeight: 500, marginBottom: 6, color: 'var(--text-2)' }}>
                                        To
                                    </label>
                                    <input
                                        type="date"
                                        value={endDate}
                                        onChange={e => setEndDate(e.target.value)}
                                        className="form-input"
                                        style={{ width: '100%' }}
                                    />
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ADMIN */}
                    {isAdmin && (
                        <div className="export-section">
                            <div className="export-section-title">
                                Researcher
                            </div>

                            <button
                                className={`export-option ${exportAll ? 'selected' : ''}`}
                                onClick={() => {
                                    setExportAll(v => !v);
                                    setSelected(null);
                                }}
                                type="button"
                                style={{ marginBottom: 8 }}
                            >
                                <div>
                                    <div className="export-option-label">
                                        All researchers
                                    </div>

                                    <div className="export-option-desc">
                                        Export metrics for every active researcher
                                    </div>
                                </div>

                                {exportAll && (
                                    <span className="export-option-check">
                                        <Icon d={ICONS.check} size={13} />
                                    </span>
                                )}
                            </button>

                            {!exportAll && (
                                <>
                                    <input
                                        className="form-input"
                                        placeholder="Search by name or email…"
                                        value={searchQuery}
                                        onChange={e => setSearch(e.target.value)}
                                        style={{ marginBottom: 8 }}
                                    />

                                    <div className="export-user-list">

                                        {loadingUsers && (
                                            <div className="export-user-empty">
                                                Loading…
                                            </div>
                                        )}

                                        {!loadingUsers && filtered.length === 0 && (
                                            <div className="export-user-empty">
                                                No researchers found.
                                            </div>
                                        )}

                                        {!loadingUsers && filtered.map(u => (
                                            <button
                                                key={u.id}
                                                className={`export-user-row ${selectedUser?.id === u.id ? 'selected' : ''}`}
                                                onClick={() => setSelected(u)}
                                                type="button"
                                            >
                                                <div
                                                    className="user-cell-avatar"
                                                    style={{
                                                        width: 28,
                                                        height: 28,
                                                        fontSize: 10,
                                                    }}
                                                >
                                                    {u.name?.slice(0, 2).toUpperCase()}
                                                </div>

                                                <div style={{ flex: 1, textAlign: 'left' }}>
                                                    <div style={{ fontSize: 13, fontWeight: 500 }}>
                                                        {u.name}
                                                    </div>

                                                    <div style={{
                                                        fontSize: 11.5,
                                                        color: 'var(--text-3)',
                                                    }}>
                                                        {u.email}
                                                    </div>
                                                </div>

                                                <Badge variant={u.role}>
                                                    {u.role}
                                                </Badge>
                                            </button>
                                        ))}
                                    </div>
                                </>
                            )}
                        </div>
                    )}
                </div>

                {/* RIGHT */}
                <div className="export-summary-card">

                    <div className="export-summary-title">
                        Export summary
                    </div>

                    <div className="export-summary-rows">

                        <div className="export-summary-row">
                            <span className="detail-label">Format</span>

                            <span style={{ fontWeight: 500 }}>
                                {format.toUpperCase()}
                            </span>
                        </div>

                        <div className="export-summary-row">
                            <span className="detail-label">Data range</span>

                            <span style={{ fontWeight: 500 }}>
                                {scope === 'history'
                                    ? 'Full history'
                                    : scope === 'latest'
                                        ? 'Latest only'
                                        : 'Custom range'}
                            </span>
                        </div>

                        {scope === 'custom' && (
                            <div className="export-summary-row">
                                <span className="detail-label">Date period</span>

                                <span style={{ fontWeight: 500, fontSize: 12 }}>
                                    {startDate || 'start'} → {endDate || 'end'}
                                </span>
                            </div>
                        )}

                        <div className="export-summary-row">
                            <span className="detail-label">Researcher</span>

                            <span style={{ fontWeight: 500 }}>
                                {exportAll
                                    ? 'All researchers'
                                    : selectedUser
                                        ? selectedUser.name
                                        : <span className="text-hint">None selected</span>}
                            </span>
                        </div>

                        <div className="export-summary-row">
                            <span className="detail-label">Columns</span>

                            <span className="text-hint" style={{ fontSize: 12 }}>
                                Name, Email, ORCID, Scholar ID, Date, Source,
                                h-index, i10-index, Citations, Publications
                            </span>
                        </div>
                    </div>

                    {success && (
                        <div className="alert alert-success" style={{ marginBottom: 12 }}>
                            <Icon d={ICONS.check} size={14} />
                            Download started successfully.
                        </div>
                    )}

                    {error && (
                        <div className="alert alert-danger" style={{ marginBottom: 12 }}>
                            {error}
                        </div>
                    )}

                    <button
                        className="btn btn-primary"
                        style={{
                            width: '100%',
                            height: 44,
                            fontSize: 14,
                        }}
                        onClick={handleExport}
                        disabled={!canExport || loading}
                    >
                        {loading
                            ? <><span className="spinner" /> Generating…</>
                            : <><Icon d={ICONS.activity} size={15} /> Export {format.toUpperCase()}</>}
                    </button>

                    {!canExport && (
                        <p
                            className="text-hint"
                            style={{
                                marginTop: 10,
                                textAlign: 'center',
                            }}
                        >
                            {isAdmin
                                ? 'Select a researcher or choose "All researchers"'
                                : 'Ready to export'}
                        </p>
                    )}
                </div>
            </div>
        </div>
    );
}