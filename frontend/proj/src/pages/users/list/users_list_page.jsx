import { useState } from 'react';
import { useUsers } from '../../../hooks/use_users.js';
import {useDeleteConfirm} from "../../../hooks/use_delete_confirm.js";
import UsersListView from "./users_list_view.jsx";

export default function UsersListPage({ onEdit, onAdd, onViewProfile, onEditMetric, onCreateMetric }) {
    const { users, loading, error, remove } = useUsers();
    const [selectedId, setSelectedId]       = useState(null);
    const [expandedMetricsId, setExpandedMetricsId] = useState(null);
    const [selectedMetricId, setSelectedMetricId] = useState(null);

    const handleRowClick = (user) => {
        setSelectedId(prev => prev === user.id ? null : user.id);
    };

    const handleEdit = (e, user) => {
        e.stopPropagation();
        if (onEdit) onEdit(user);
    };

    const handleCancel = (e) => {
        e?.stopPropagation();
        setSelectedId(null);
        setSelectedMetricId(null);
        setExpandedMetricsId(null);
    };

    const handleViewProfile = (user) => {
        const profile = user.researcherProfile ?? null;

        onViewProfile?.({
            user: user,
            profile: profile,
        });
    };

    const {
        deleteTarget,
        deleting,
        handleDeleteClick,
        handleDeleteConfirm,
        handleDeleteCancel,
    } = useDeleteConfirm(remove, () => setSelectedId(null));

    return (
        <UsersListView
            users={users}
            loading={loading}
            error={error}
            selectedId={selectedId}
            expandedMetricsId={expandedMetricsId}
            deleteTarget={deleteTarget}
            deleting={deleting}
            onAdd={onAdd}
            onRowClick={handleRowClick}
            onEdit={handleEdit}
            onDeleteClick={handleDeleteClick}
            onCancel={handleCancel}
            onDeleteConfirm={handleDeleteConfirm}
            onDeleteCancel={handleDeleteCancel}
            onViewProfile={handleViewProfile}
            onExpandMetrics={(userId) => setExpandedMetricsId(prev => prev === userId ? null : userId)}
            onEditMetric={onEditMetric}
            onCreateMetric={onCreateMetric}
        />
    );
}