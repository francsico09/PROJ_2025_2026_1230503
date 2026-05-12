const PAGE_TITLES = {
    'dashboard':              'Dashboard',
    'aggregated-dashboard':   'Aggregated Dashboard',
    'personal-dashboard':     'Individual Dashboard',

    'manage-users':           'Users',
    'edit-user':              'Users · Edit',
    'create-user':            'Users · Create',

    'manage-metrics':         'Metrics',
    'edit-metric':            'Metrics · Edit',
    'create-metric':          'Metrics · Create',

    'manage-profiles':        'Profiles',
    'edit-profile':           'Profiles · Edit',
    'profile-form':           'Profiles · Create',

    'export':                 'Export Metrics',
};

export default function Topbar({ page }) {
    return (
        <header className="topbar">
            <span className="topbar-title">{PAGE_TITLES[page] ?? page}</span>
        </header>
    );
}