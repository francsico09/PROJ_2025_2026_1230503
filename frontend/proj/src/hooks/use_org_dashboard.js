import { useState, useEffect, useCallback } from 'react';
import {getLatestByUser} from "../api/metrics.js";
import {getAggAverages} from "../api/aggregated_metrics.js";

/**
 * A custom hook to manage the state and data fetching for the organization dashboard.
 *
 * @returns {{latestByResearcher: *[], averages: unknown, availableSources: *[], selectedSource: unknown, setSelectedSource: (value: unknown) => void, loading: boolean, error: unknown, refresh: function(): Promise<void>}}
 */
export function useOrgDashboard() {
    const token = localStorage.getItem('token');

    const [latestByResearcher, setLatestByResearcher] = useState([]);
    const [averages, setAverages]                     = useState(null);
    const [availableSources, setAvailableSources]     = useState([]);
    const [selectedSource, setSelectedSource]         = useState(null);
    const [loading, setLoading]                       = useState(true);
    const [error, setError]                           = useState(null);

    // 1. Carrega fontes disponíveis a partir das métricas mais recentes (sem filtro de fonte)
    const fetchSources = useCallback(async () => {
        try {
            const data = await getLatestByUser(token);
            const metrics = Array.isArray(data) ? data : [];
            const sources = [...new Set(metrics.map(m => m.source?.name).filter(Boolean))].sort();
            setAvailableSources(sources.map(name => ({ name })));
            if (sources.length > 0) setSelectedSource(prev => prev ?? sources[0]);
        } catch {
            setError('Failed to load available sources.');
        }
    }, [token]);

    // 2. Quando a fonte muda, busca latest e averages para essa fonte
    const fetchForSource = useCallback(async (source) => {
        if (!source) return;
        setLoading(true);
        setError(null);
        try {
            const [latest, avgs] = await Promise.all([
                getLatestByUser(token, source),
                getAggAverages(token, source),
            ]);
            setLatestByResearcher(Array.isArray(latest) ? latest : []);
            setAverages(avgs);
        } catch {
            setError('Failed to load organisation metrics.');
        } finally {
            setLoading(false);
        }
    }, [token]);

    useEffect(() => { fetchSources(); }, [fetchSources]);

    useEffect(() => {
        if (selectedSource) fetchForSource(selectedSource);
    }, [selectedSource, fetchForSource]);

    return {
        latestByResearcher,
        averages,
        availableSources,
        selectedSource,
        setSelectedSource,
        loading,
        error,
        refresh: () => fetchForSource(selectedSource),
    };
}