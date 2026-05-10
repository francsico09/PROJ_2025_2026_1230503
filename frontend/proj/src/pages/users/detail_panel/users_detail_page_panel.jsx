import Badge from '../../../components/badge.jsx';
import Icon, { ICONS } from '../../../components/icon.jsx';

function DetailRow({ label, value }) {
    return (
        <div className="detail-row">
            <span className="detail-label">{label}</span>
            <span className="detail-value">{value ?? '—'}</span>
        </div>
    );
}

export default function UserDetailPanel({ user, onEdit, onClose }) {
    const initials = user.name
        ?.split(' ')
        .map(w => w[0])
        .slice(0, 2)
        .join('')
        .toUpperCase();

    return (
        <aside className="detail-panel">
            {/* Header */}
            <div className="detail-panel-header">
                <span className="text-hint">User details</span>
                <button className="btn btn-ghost" style={{ padding: '0 6px', height: 28 }} onClick={onClose}>
                    <Icon d={ICONS.close} size={14} />
                </button>
            </div>

            {/* Profile block */}
            <div className="detail-profile">
                <div className="detail-avatar">{initials}</div>
                <div>
                    <div className="detail-name">{user.name}</div>
                    <div className="detail-email">{user.email}</div>
                    <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
                        <Badge variant={user.role}>{user.role}</Badge>
                        <Badge variant={user.active ? 'active' : 'inactive'}>
                            {user.active ? 'active' : 'inactive'}
                        </Badge>
                    </div>
                </div>
            </div>

            <div className="detail-divider" />

            {/* Fields */}
            <div className="detail-fields">
                <DetailRow label="ID" value={<span className="mono">{user.id}</span>} />
                <DetailRow label="Name" value={user.name} />
                <DetailRow label="Email" value={user.email} />
                <DetailRow label="Role" value={user.role} />
                <DetailRow label="Active" value={user.active ? 'Yes' : 'No'} />
                {user.researcherProfile && (
                    <DetailRow label="Profile ID" value={
                        <span className="mono">{user.researcherProfile}</span>
                    } />
                )}
            </div>

            <div className="detail-divider" />

            {/* Actions */}
            <div className="detail-actions">
                <button className="btn btn-primary" style={{ flex: 1 }} onClick={onEdit}>
                    <Icon d={ICONS.edit} size={14} />
                    Edit user
                </button>
                <button className="btn btn-outline" onClick={onClose}>
                    Close
                </button>
            </div>
        </aside>
    );
}