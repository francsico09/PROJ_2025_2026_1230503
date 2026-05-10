import { useState } from 'react';
import { useUserDashboardMetrics } from '../../../hooks/use_user_dashboard_metrics.js';
import IndividualDashboardView from './dashboard_individual_view.jsx';

export default function IndividualDashboardPage() {
    const currentUser = (() => {
        try {
            const u = localStorage.getItem('user');
            return u ? JSON.parse(u) : null;
        } catch {
            return null;
        }
    })();

    const isAdmin = currentUser?.role === 'admin';
    const [selectedUserId, setSelectedUserId] = useState(isAdmin ? null : currentUser?.id);

    const dashboardUserId = isAdmin ? selectedUserId : currentUser?.id;

    const {
        allMetrics,
        currentMetric,
        loading,
        error,
        selectedSource,
        setSelectedSource,
        availableSources,
    } = useUserDashboardMetrics(dashboardUserId);

    return (
        <IndividualDashboardView
            isAdmin={isAdmin}
            selectedUserId={selectedUserId}
            setSelectedUserId={setSelectedUserId}
            allMetrics={allMetrics}
            currentMetric={currentMetric}
            loading={loading}
            error={error}
            selectedSource={selectedSource}
            setSelectedSource={setSelectedSource}
            availableSources={availableSources}
        />
    );
}