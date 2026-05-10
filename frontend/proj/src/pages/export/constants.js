export const FORMAT_OPTIONS = [
    {
        value: 'xlsx',
        label: 'Excel',
        description: 'Formatted spreadsheet with styled headers',
        icon: '⊞',
    },
    {
        value: 'csv',
        label: 'CSV',
        description: 'Plain text, compatible with any tool',
        icon: '≡',
    },
];

export const SCOPE_OPTIONS = [
    {
        value: 'history',
        label: 'Full history',
        description: 'All collected metrics over time',
    },
    {
        value: 'latest',
        label: 'Latest only',
        description: 'Most recent entry per source',
    },
    {
        value: 'custom',
        label: 'Custom range',
        description: 'Metrics within a specific date range',
    },
];