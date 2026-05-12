import Icon, {ICONS} from './icon.jsx';

const NAV_ITEMS = [
    {
        key: 'dashboard', label: 'Dashboard', icon: ICONS.dashboard,
        children: [
            {key: 'aggregated-dashboard', label: 'Aggregated Dashboard', icon: ICONS.activity},
            {key: 'personal-dashboard', label: 'Personal Dashboard', icon: ICONS.dashboard},
        ]
    },
    {key: 'manage-users', label: 'Manage users', icon: ICONS.users, roles: ['admin']},
    {key: 'my-user-profile', label: 'My Profile', icon: ICONS.users},
    {key: 'export', label: 'Export Metrics', icon: ICONS.metrics},
];

const isChildActive = (item, active) =>
    item.children?.some(c => c.key === active);

export default function Sidebar({active, onNavigate, onLogout, user}) {

    const hasRole = (item) => {
        if (!item.roles) return true;

        if (!user || !user.role) return false;

        const userRole = user.role.toLowerCase();
        return item.roles.some(role => role.toLowerCase() === userRole);
    };

    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <h1 className="sidebar-logo-title">RIP</h1>
                <p className="sidebar-logo-sub">Research Intelligence</p>
            </div>

            {user && (
                <div className="sidebar-user">
                    <div className="user-avatar">{user.initials}</div>
                    <div className="user-info">
                        <div className="user-name">{user.name}</div>
                        <div className="user-role">{user.role}</div>
                    </div>
                </div>
            )}

            <nav className="sidebar-nav">
                <span className="nav-section-label">Navigation</span>

                {NAV_ITEMS.filter(hasRole).map(item => {
                    const isActive = active === item.key || isChildActive(item, active);
                    const firstChild = item.children?.[0]?.key;

                    return (
                        <div key={item.key}>
                            <div
                                className={`nav-item ${isActive ? 'active' : ''}`}
                                onClick={() => onNavigate(firstChild ?? item.key)}
                            >
                <span className="nav-icon">
                  <Icon d={item.icon} size={15}/>
                </span>
                                {item.label}
                            </div>

                            {item.children && isActive &&
                                item.children.map(child => (
                                    <div
                                        key={child.key}
                                        className={`nav-item nav-item-sub ${active === child.key ? 'active' : ''}`}
                                        onClick={() => onNavigate(child.key)}
                                    >
                                        {child.label}
                                    </div>
                                ))
                            }
                        </div>
                    );
                })}
            </nav>

            <div className="sidebar-bottom">
                <button className="logout-btn" onClick={onLogout}>
                    <Icon d={ICONS.logout} size={14}/>
                    Sign out
                </button>
            </div>
        </aside>
    );
}