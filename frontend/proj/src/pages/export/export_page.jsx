import { useState } from 'react';
import { useUsers } from '../../hooks/use_users.js';
import { exportResearcherMetrics, exportAllMetrics } from '../../api/export.js';
import ExportView from './export_view.jsx';

export default function ExportPage({ currentUser }) {
    const isAdmin = currentUser?.role === 'admin';

    const { users, loading: loadingUsers } = useUsers();
    const researchers = users?.filter(u => u.active) ?? [];

    const [format, setFormat] = useState('xlsx');
    const [scope, setScope] = useState('history');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [searchQuery, setSearch] = useState('');
    const [selectedUser, setSelected] = useState(
        isAdmin ? null : currentUser
    );
    const [exportAll, setExportAll] = useState(false);
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState(null);

    const filtered = researchers.filter(u =>
        u.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        u.email.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const canExport = exportAll || !!selectedUser;

    const handleExport = async () => {
        setLoading(true);
        setSuccess(false);
        setError(null);

        const token = localStorage.getItem('token');

        try {
            const dateParams = {
                startDate: scope === 'custom' && startDate ? startDate : undefined,
                endDate: scope === 'custom' && endDate ? endDate : undefined,
            };

            if (exportAll && isAdmin) {
                await exportAllMetrics(format, scope, token, dateParams);
            } else if (selectedUser) {
                await exportResearcherMetrics(selectedUser.id, format, scope, token, dateParams);
            }

            setSuccess(true);
        } catch (err) {
            setError(err.message || 'Export failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <ExportView
            isAdmin={isAdmin}
            format={format}
            setFormat={setFormat}
            scope={scope}
            setScope={setScope}
            startDate={startDate}
            setStartDate={setStartDate}
            endDate={endDate}
            setEndDate={setEndDate}
            searchQuery={searchQuery}
            setSearch={setSearch}
            selectedUser={selectedUser}
            setSelected={setSelected}
            exportAll={exportAll}
            setExportAll={setExportAll}
            loading={loading}
            success={success}
            error={error}
            loadingUsers={loadingUsers}
            filtered={filtered}
            canExport={canExport}
            handleExport={handleExport}
        />
    );
}