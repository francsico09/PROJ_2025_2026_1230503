import { useState, useEffect, useCallback } from 'react';

import {
    createMetric,
    updateMetric,
    deleteMetric,
    fetchMetricByUser,
} from '../api/metrics.js';

/**
 * A custom hook to manage researcher metrics, including fetching, creating,
 * updating and removing
 *
 * @param researcherId
 * @param initialPageSize
 * @returns {{items: *[], total: number, pages: number, page: number, setPage: (value: (((prevState: number) => number) | number)) => void, search: string, setSearch: (value: (((prevState: string) => string) | string)) => void, loading: boolean, error: unknown, create: function(*): Promise<unknown>, update: function(*, *): Promise<unknown>, remove: (function(*): Promise<void>)|*, refresh: (function(): Promise<void>)|*}}
 */
export function useResearcherMetrics(researcherId, { initialPageSize = 20 } = {}) {
    const [items, setItems] = useState([]);
    const [total, setTotal] = useState(0);
    const [pages, setPages] = useState(0);
    const [page, setPage] = useState(1);
    const [pageSize] = useState(initialPageSize);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const token = localStorage.getItem('token');

    const fetchMetrics = useCallback(async () => {
        if (!researcherId) {
            setItems([]);
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const data = await fetchMetricByUser(
                researcherId,
                token,
                {
                    page,
                    pageSize,
                    search,
                }
            );
            setItems(data.items ?? []);
            setTotal(data.total ?? 0);
            setPages(data.pages ?? 0);

        } catch (err) {
            console.error(err);

            setError('Failed to load researcher metrics.');
            setItems([]);

        } finally {
            setLoading(false);
        }
    }, [
        researcherId,
        token,
        page,
        pageSize,
        search,
    ]);

    useEffect(() => {
        fetchMetrics();
    }, [fetchMetrics]);

    const create = async (data) => {
        if (!researcherId)
            throw new Error('Researcher ID is required');

        const created = await createMetric(data, token);

        setItems(prev => [created, ...prev]);

        return created;
    };

    const update = async (id, data) => {
        const updated = await updateMetric(id, data, token);

        setItems(prev =>
            prev.map(m => m.id === id ? updated : m)
        );

        return updated;
    };

    const remove = async (id) => {
        await deleteMetric(id, token);

        setItems(prev =>
            prev.filter(m => m.id !== id)
        );
    };

    return {
        items,
        total,
        pages,
        page,
        setPage,
        search,
        setSearch,
        loading,
        error,
        create,
        update,
        remove,
        refresh: fetchMetrics,
    };
}