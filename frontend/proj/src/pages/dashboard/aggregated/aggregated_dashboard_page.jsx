import AggregatedDashboardView from "./aggregated_dashboard_view.jsx";
import { useUsers } from "../../../hooks/use_users.js";
import { useOrgDashboard } from "../../../hooks/use_org_dashboard.js";

const EXCLUDED_USERS = ['Zita Vale'];

export default function AggregatedDashboardPage() {

    const {
        latestByResearcher,
        averages,
        availableSources,
        selectedSource,
        setSelectedSource,
        selectedMetric,
        setSelectedMetric,
        loading: loadingMetrics,
        error,
    } = useOrgDashboard();

    const {
        users: usersData,
        loading: loadingUsers,
    } = useUsers({
        initialPageSize: 100,
        exclude_names: EXCLUDED_USERS
    });

    const researchersList = usersData?.filter(u => u.role === 'researcher' && u.active) ?? [];

    return (
        <AggregatedDashboardView
            users={researchersList}
            latestByResearcher={latestByResearcher}
            averages={averages}
            availableSources={availableSources}
            selectedSource={selectedSource}
            onSourceChange={setSelectedSource}
            selectedMetric={selectedMetric}
            onMetricChange={setSelectedMetric}
            loadingMetrics={loadingMetrics || loadingUsers}
            error={error}
        />
    );
}