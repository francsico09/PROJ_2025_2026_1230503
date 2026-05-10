import { useState, useEffect, useCallback } from 'react';
import { getMetrics } from '../api/metrics.js';

export function useOrgDashboard() {
    const [allMetrics, setAllMetrics]   = useState([]);
    const [loading, setLoading]         = useState(true);
    const [error, setError]             = useState(null);
    const [selectedSource, setSelectedSource] = useState(null);
    const token = localStorage.getItem('token');

    const fetchMetrics = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await getMetrics(token);
            const metrics = Array.isArray(data) ? data : [];
            setAllMetrics(metrics);

            if (metrics.length > 0) {
                const sources = [...new Set(metrics.map(m => m.source?.name).filter(Boolean))].sort();
                if (sources.length > 0) setSelectedSource(sources[0]);
            }
        } catch {
            setError('Failed to load organisation metrics.');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchMetrics(); }, [fetchMetrics]);

    const availableSources = [...new Set(
        allMetrics.map(m => m.source?.name).filter(Boolean)
    )].sort().map(name => ({ name }));

    const filteredMetrics = selectedSource
        ? allMetrics.filter(m => m.source?.name === selectedSource)
        : allMetrics;

    const latestByResearcher = Object.values(
        filteredMetrics.reduce((acc, m) => {
            const rid = m.researcher_id;
            if (!acc[rid] || new Date(m.date) > new Date(acc[rid].date)) {
                acc[rid] = m;
            }
            return acc;
        }, {})
    );

    const averages = _calcAverages(latestByResearcher);

    return {
        allMetrics,
        filteredMetrics,
        latestByResearcher,
        averages,
        availableSources,
        selectedSource,
        setSelectedSource,
        loading,
        error,
        refresh: fetchMetrics,
    };
}

function _calcAverages(metrics) {
    if (metrics.length === 0) return null;

    const sum = (key) => metrics.reduce((acc, m) => acc + (m[key] ?? 0), 0);
    const avg = (key) => Math.round(sum(key) / metrics.length);

    return {
        h_index:            avg('h_index'),
        i10_index:          avg('i10_index'),
        total_citations:    avg('total_citations'),
        total_publications: avg('total_publications'),
        h_index_5y:         avg('h_index_5y'),
        citations_5y:       avg('citations_5y'),
        count:              metrics.length,
    };
}