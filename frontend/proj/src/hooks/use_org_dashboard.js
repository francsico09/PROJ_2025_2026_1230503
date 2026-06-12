import {useState, useEffect, useCallback, useRef} from 'react';
import { getLatestByUser } from "../api/metrics.js";
import { getAggAverages } from "../api/aggregated_metrics.js";
import { fetchUsers } from "../api/users.js";

export function useOrgDashboard() {
    const token = useRef(localStorage.getItem('token'));

    const [users, setUsers] = useState({ items: [], total: 0 }); // ← Novo estado para os utilizadores
    const [latestByResearcher, setLatestByResearcher] = useState([]);
    const [averages, setAverages] = useState(null);
    const [availableSources, setAvailableSources] = useState([]);
    const [selectedSource, setSelectedSource] = useState(null);
    const [selectedMetric, setSelectedMetric] = useState('h_index');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchSourcesAndUsers = useCallback(async () => {
        try {
            const [metricsData, usersData] = await Promise.all([
                getLatestByUser(token.current, '', { pageSize: 100 }),
                fetchUsers(token.current, { page: 1, pageSize: 100 })
            ]);

            setUsers(usersData ?? { items: [], total: 0 });

            const metrics = metricsData?.items ?? [];
            const sources = [...new Set(metrics.map(m => m.source?.name).filter(Boolean))].sort();

            setAvailableSources(sources.map(name => ({ name })));

            if (sources.length > 0) {
                setSelectedSource(prev => prev ?? sources[0]);
            } else {
                setLoading(false);
            }

        } catch (err) {
            setError('Failed to load initial configuration data.');
            setLoading(false);
        }
    }, []);

    const fetchForSourceAndMetric = useCallback(async (source, metric) => {
        if (!source) return;
        setLoading(true);
        setError(null);
        try {
            const [latestData, avgs] = await Promise.all([
                getLatestByUser(token.current, source, { sortBy: metric, sortDir: 'desc', pageSize: 10, page: 1 }),
                getAggAverages(token.current, source),
            ]);

            const latestArray = latestData?.items ?? [];
            setLatestByResearcher(latestArray);
            setAverages(avgs);
        } catch {
            setError('Failed to load organisation metrics.');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchSourcesAndUsers();
    }, [fetchSourcesAndUsers]);

    useEffect(() => {
        if (selectedSource) {
            fetchForSourceAndMetric(selectedSource, selectedMetric);
        }
    }, [selectedSource, selectedMetric, fetchForSourceAndMetric]);

    return {
        users,
        latestByResearcher,
        averages,
        availableSources,
        selectedSource,
        setSelectedSource,
        selectedMetric,
        setSelectedMetric,
        loading,
        error,
        refresh: () => fetchForSourceAndMetric(selectedSource, selectedMetric),
    };
}