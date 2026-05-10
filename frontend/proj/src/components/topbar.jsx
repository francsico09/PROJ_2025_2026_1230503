const PAGE_TITLES = {
    'dashboard':              'Dashboard',
    'extraction-individual':  'Extraction · Individual',
    'extraction-all':         'Extraction · All users',
    'manage-users':           'Users',
    'edit-user':              'Users · Edit',
    'manage-metrics':         'Metrics',
    'edit-metric':            'Metrics · Edit',
    'manage-profiles':        'Profiles',
    'edit-profile':           'Profiles · Edit',
    'aggregated-dashboard':   'Aggregated Dashboard',
    'personal-dashboard':     'Individual Dashboard',
    'export':                 'Export Metrics',
};

export default function Topbar({ page }) {
    return (
        <header className="topbar">
            <span className="topbar-title">{PAGE_TITLES[page] ?? page}</span>
        </header>
    );
}