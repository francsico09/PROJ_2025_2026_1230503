import { useState, useEffect, useCallback } from 'react';
import { getMetricsByUserId } from '../api/metrics.js';

/**
 * Hook to fetch and manage metrics for the current user's dashboard
 * Allows filtering by source
 */
export function useUserDashboardMetrics(userId) {
    const [allMetrics, setAllMetrics] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [selectedSource, setSelectedSource] = useState(null);

    const token = localStorage.getItem('token');

    const fetchMetrics = useCallback(async () => {
        if (!userId) return;

        setLoading(true);
        setError(null);

        try {
            const data = await getMetricsByUserId(userId, token);
            const metricsArray = Array.isArray(data) ? data : [];
            setAllMetrics(metricsArray);

            if (metricsArray.length > 0 && !selectedSource) {
                const uniqueSources = [...new Map(
                    metricsArray
                        .sort((a, b) => new Date(b.date) - new Date(a.date))
                        .map(m => [m.source.name, m.source])
                ).values()];

                if (uniqueSources.length > 0) {
                    setSelectedSource(uniqueSources[0].name);
                }
            }

        } catch (err) {
            setError('Failed to load metrics.');
            setAllMetrics([]);

        } finally {
            setLoading(false);

        }
    }, [userId, token]);

    useEffect(() => {
        fetchMetrics();
    }, [fetchMetrics]);

    const availableSources = Array.from(
        new Map(allMetrics.map(m => [m.source.name, m.source])).values()
    ).sort((a, b) => a.name.localeCompare(b.name));

    const filteredMetrics = selectedSource
        ? allMetrics.filter(m => m.source.name === selectedSource)
        : allMetrics;

    const sortedMetrics = [...filteredMetrics]
        .sort((a, b) =>
            new Date(b.date).getTime() - new Date(a.date).getTime()
    );
    console.log('sorted:', sortedMetrics.map(m => m.date));

    const currentMetric = sortedMetrics.length > 0 ? sortedMetrics[0] : null;

    return {
        allMetrics,
        filteredMetrics,
        sortedMetrics,
        currentMetric,
        loading,
        error,
        selectedSource,
        setSelectedSource,
        availableSources,
        refresh: fetchMetrics,
    };
}

