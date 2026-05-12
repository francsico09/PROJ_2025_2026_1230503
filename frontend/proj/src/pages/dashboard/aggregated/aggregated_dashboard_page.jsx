import { useUsers } from '../../../hooks/use_users.js';
import { useOrgDashboard } from "../../../hooks/use_org_dashboard.js";
import AggregatedDashboardView from './aggregated_dashboard_view.jsx';

/**
 * AggregatedDashboardPage is the main component for the aggregated dashboard page.
 * It fetches the necessary data using custom hooks and passes it to the view component.
 *
 * @returns {React.JSX.Element}
 * @constructor
 */
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

    const {
        users,
        loading: loadingUsers,
        page,
        pages,
        setPage,
    } = useUsers({ initialPageSize: 10 });

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
            page={page}
            pages={pages}
            onPageChange={setPage}
        />
    );
}