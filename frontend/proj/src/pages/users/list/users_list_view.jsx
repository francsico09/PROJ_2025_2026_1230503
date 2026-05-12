import { Fragment } from 'react';
import Badge from '../../../components/badge.jsx';
import Icon, { ICONS } from '../../../components/icon.jsx';
import ConfirmDialog from '../../../components/confirm_dialog.jsx';
import Pagination from '../../../components/paginations.jsx';
import ResearcherMetricsUserRow from './user_metrics/researcher_metrics_user_row.jsx';

export default function UsersListView({
                                          users,
                                          loading,
                                          error,
                                          selectedId,
                                          expandedMetricsId,
                                          deleteTarget,
                                          deleting,
                                          onAdd,
                                          onRowClick,
                                          onEdit,
                                          onDeleteClick,
                                          onCancel,
                                          onDeleteConfirm,
                                          onDeleteCancel,
                                          onViewProfile,
                                          onExpandMetrics,
                                          onEditMetric,
                                          onCreateMetric,
                                          page,
                                          pages,
                                          onPageChange,
                                          search,
                                          onSearchChange,
                                      }) {
    return (
        <div>
            <div className="page-header">
                <h2>Users</h2>
                <p>All registered users. Click a row to preview, then edit.</p>
            </div>

            <div className="card">
                <div className="card-header">
                    <h3>{loading ? '—' : `${users?.length || 0} users on this page`}</h3>
                    <button className="btn btn-primary" onClick={onAdd}>
                        <Icon d={ICONS.plus} size={14}/>
                        New user
                    </button>
                </div>

                {error && (
                    <div className="alert alert-danger" style={{ margin: '16px 20px' }}>
                        {error}
                    </div>
                )}

                {/* ── Search Bar ── */}
                <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
                    <input
                        type="text"
                        placeholder="Search by name or email…"
                        value={search}
                        onChange={(e) => onSearchChange(e.target.value)}
                        style={{
                            width: '100%',
                            padding: '10px 12px',
                            border: '1px solid var(--border)',
                            borderRadius: '6px',
                            fontSize: '14px',
                            fontFamily: 'inherit',
                        }}
                    />
                </div>

                <table>
                    <thead>
                    <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Status</th>
                        <th></th>
                    </tr>
                    </thead>

                    <tbody>
                    {loading && (
                        <tr className="loading-row">
                            <td colSpan={5}>Loading users…</td>
                        </tr>
                    )}

                    {!loading && users?.length === 0 && (
                        <tr className="loading-row">
                            <td colSpan={5}>No users found.</td>
                        </tr>
                    )}

                    {!loading && users?.map(user => (
                        <Fragment key={user.id}>
                            <tr
                                onClick={() => onRowClick(user)}
                                className={selectedId === user.id ? 'row-selected' : ''}
                            >
                                <td>
                                    <div className="user-cell">
                                        <div className="user-cell-avatar">
                                            {user.name?.slice(0, 2).toUpperCase()}
                                        </div>
                                        <span className="user-cell-name">{user.name}</span>
                                    </div>
                                </td>
                                <td className="text-muted">{user.email}</td>
                                <td><Badge variant={user.role}>{user.role}</Badge></td>
                                <td>
                                    <Badge variant={user.active ? 'active' : 'inactive'}>
                                        {user.active ? 'active' : 'inactive'}
                                    </Badge>
                                </td>
                                <td style={{ textAlign: 'right' }}>
                                    <Icon
                                        d={ICONS.chevronR}
                                        size={14}
                                        style={{
                                            color: 'var(--text-3)',
                                            transform: selectedId === user.id ? 'rotate(90deg)' : 'none',
                                            transition: 'transform 0.15s',
                                        }}
                                    />
                                </td>
                            </tr>

                            {selectedId === user.id && (
                                <tr className="dropdown-row">
                                    <td colSpan={5}>
                                        <div className="user-dropdown-inner">

                                            {/* ── Toolbar ── */}
                                            <div className="user-dropdown-toolbar">
                                                {/* Left — researcher_metric toggle */}
                                                <div className="user-dropdown-toolbar-left">
                                                    {user.researcherProfile && (
                                                        <button
                                                            className="btn btn-outline"
                                                            onClick={() => onExpandMetrics(user.id)}
                                                        >
                                                            <Icon
                                                                d={expandedMetricsId === user.id ? ICONS.metrics : ICONS.metrics}
                                                                size={13}
                                                            />
                                                            {expandedMetricsId === user.id ? 'Hide researcher_metric' : 'View researcher_metric'}
                                                        </button>
                                                    )}
                                                </div>

                                                {/* Right — actions */}
                                                <div className="user-dropdown-toolbar-right">
                                                    <button
                                                        className="btn btn-primary"
                                                        onClick={(e) => onEdit(e, user)}
                                                    >
                                                        <Icon d={ICONS.edit} size={13}/>
                                                        Edit
                                                    </button>

                                                    <button
                                                        className="btn btn-primary"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            onViewProfile(user);
                                                        }}
                                                    >
                                                        <Icon d={ICONS.profiles} size={13}/>
                                                        {user.researcherProfile ? 'Edit profile' : 'Create profile'}
                                                    </button>

                                                    <button
                                                        className="btn btn-danger"
                                                        onClick={(e) => onDeleteClick(e, user)}
                                                    >
                                                        <Icon d={ICONS.trash} size={13}/>
                                                        Delete
                                                    </button>

                                                    <button
                                                        className="btn btn-outline"
                                                        onClick={onCancel}
                                                    >
                                                        Close
                                                    </button>
                                                </div>
                                            </div>

                                            {/* ── Metrics table ── */}
                                            {user.researcherProfile && expandedMetricsId === user.id && (
                                                <div className="user-dropdown-metrics">
                                                    <ResearcherMetricsUserRow
                                                        user={user}
                                                        expandedMetricsId={expandedMetricsId}
                                                        onExpandMetrics={onExpandMetrics}
                                                        onEditMetric={onEditMetric}
                                                        onCreateMetric={onCreateMetric}
                                                        showOnlyTable={true}
                                                    />
                                                </div>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            )}
                        </Fragment>
                    ))}
                    </tbody>
                </table>

                {pages > 1 && (
                    <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border)' }}>
                        <Pagination
                            page={page}
                            pages={pages}
                            onPageChange={onPageChange}
                        />
                    </div>
                )}
            </div>

            <ConfirmDialog
                open={!!deleteTarget}
                title="Delete user?"
                message={`This will permanently delete ${deleteTarget?.name}. This action cannot be undone.`}
                confirmLabel={deleting ? 'Deleting…' : 'Delete user'}
                onConfirm={onDeleteConfirm}
                onCancel={onDeleteCancel}
            />
        </div>
    );
}