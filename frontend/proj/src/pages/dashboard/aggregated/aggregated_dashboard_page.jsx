import { useUsers } from '../../../hooks/use_users.js';
import { useOrgDashboard } from "../../../hooks/use_org_dashboard.js";

import AggregatedDashboardView from './aggregated_dashboard_view.jsx';

export default function AggregatedDashboardPage() {
    const {
        latestByResearcher,
        averages,
        availableSources,
        selectedSource,
        setSelectedSource,
        loading: loadingMetrics,
        error,
    } = useOrgDashboard();

    const { users, loading: loadingUsers } = useUsers();

    const researchers =
        users?.filter(u => u.role === 'researcher' && u.active) ?? [];

    return (
        <AggregatedDashboardView
            researchers={researchers}
            latestByResearcher={latestByResearcher}
            averages={averages}
            availableSources={availableSources}
            selectedSource={selectedSource}
            onSourceChange={setSelectedSource}
            loadingMetrics={loadingMetrics}
            loadingUsers={loadingUsers}
            error={error}
        />
    );
}