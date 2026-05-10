import { useState, useEffect, useCallback } from 'react';
import { getMetricsByUserId, createMetric, updateMetric, deleteMetric } from '../api/metrics.js';

export function useResearcherMetrics(researcherId) {
    const [metrics, setMetrics] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const token = localStorage.getItem('token');

    const fetchMetrics = useCallback(async () => {
        if (!researcherId) {
            setMetrics([]);
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const data = await getMetricsByUserId(researcherId, token);
            setMetrics(Array.isArray(data) ? data : []);

        } catch (err) {
            setError('Couldn\'t load researcher metrics.');
            setMetrics([]);

        } finally {
            setLoading(false);
        }
    }, [researcherId, token]);

    useEffect(() => {
        fetchMetrics();
    }, [fetchMetrics]);

    const create = async (data) => {
        if (!researcherId)
            throw new Error('Researcher ID is required');

        const created = await createMetric(data, token);
        setMetrics(prev => [...prev, created]);

        return created;
    };

    const update = async (id, data) => {
        const updated = await updateMetric(id, data, token);
        setMetrics(prev => prev.map(m => m.id === id ? updated : m));

        return updated;
    };

    const remove = async (id) => {
        await deleteMetric(id, token);
        setMetrics(prev => prev.filter(m => m.id !== id));
    };

    return {
        metrics,
        loading,
        error,
        create,
        update,
        remove,
        refresh: fetchMetrics
    };
}

