import { useState, useEffect, useCallback } from 'react';
import {fetchMetricByUser} from '../api/metrics.js';

/**
 * A custom hook to manage researcher metrics for a user dashboard
 *
 * @param userId
 * @returns {{allMetrics: *[], filteredMetrics: *[], sortedMetrics: *[], currentMetric: *, loading: boolean, error: unknown, selectedSource: unknown, setSelectedSource: (value: unknown) => void, availableSources: undefined[], refresh: (function(): Promise<void>)|*}}
 */
export function useUserDashboardMetrics(userId) {
    const [allMetrics, setAllMetrics] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [selectedSource, setSelectedSource] = useState(null);

    const token = localStorage.getItem('token');

    const fetchMetrics = useCallback(async () => {
        if (!userId) {
            return;
        }

        setLoading(true);
        setError(null);
        setAllMetrics([]);
        setSelectedSource(null);

        try {
            const data = await fetchMetricByUser(userId, token,
                {
                    page: 1,
                    pageSize: 100
                });
            const metricsArray = data.items ?? [];
            setAllMetrics(metricsArray);

            if (metricsArray.length > 0) {
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
            setError('Failed to load researcher metrics.');
            setAllMetrics([]);
        } finally {
            setLoading(false);
        }
    }, [userId, token]);

    useEffect(() => {
        fetchMetrics();
    }, [userId]);

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

