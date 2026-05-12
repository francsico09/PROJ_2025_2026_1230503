const BASE = '/api/v1/researcher_metrics';

export const createMetric = (data, token) =>
    fetch(`${BASE}/create_metric`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(data),
    }).then(async r => {
        if (!r.ok)
            throw new Error((await r.json()).detail || 'Failed');

        return r.json();
    });

export const deleteMetric = (id, token) =>
    fetch(`${BASE}/${id}`, {
        method: 'DELETE',
        headers: {
            Authorization: `Bearer ${token}`,
        },
    }).then(async r => {
        if (!r.ok)
            throw new Error((await r.json()).detail || 'Failed');
    });

export const updateMetric = (id, data, token) =>
    fetch(`${BASE}/${id}`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(data),
    }).then(async r => {
        if (!r.ok)
            throw new Error((await r.json()).detail || 'Failed');

        return r.json();
    });

export const fetchMetricByUser = (
    userId,
    token,
    {
        page = 1,
        pageSize = 20,
        search = '',
        sortBy = 'date',
        sortDir = 'desc',
    } = {}
) => {

    const params = new URLSearchParams({
        page,
        page_size: pageSize,
        search,
        sort_by: sortBy,
        sort_dir: sortDir,
    });
    return fetch(
        `${BASE}/by-user/${userId}?${params}`,
        {
            method: 'GET',
            headers: {
                Authorization: `Bearer ${token}`,
            },
        }
    ).then(async r => {
        if (!r.ok)
            throw new Error((await r.json()).detail || 'Failed');

        return r.json();
    });
};

export const getLatestByUser = (token, source = '') => {
    const params = new URLSearchParams();

    if (source) {
        params.append('source', source);
    }

    return fetch(`${BASE}/latest-by-user?${params}`, {
        method: 'GET',
        headers: {
            Authorization: `Bearer ${token}`,
        },
    }).then(async (r) => {
        if (!r.ok) {
            const err = await r.json().catch(() => ({}));
            throw new Error(err.detail || 'Failed to fetch latest metrics');
        }
        return r.json();
    });
};