const BASE = '/api/v1/researcher_metrics';

export const getMetrics = (token) =>
    fetch(`${BASE}/`, {
        headers: {
            'Authorization': `Bearer ${token}`
        },
    }).then(r => r.json());

export const getMetricsByUserId = (userId, token) =>
    fetch(`${BASE}/by-user/${userId}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        },
    }).then(r => r.json());

export const getMetricsByDate = (date, token) =>
    fetch(`${BASE}/by-date/${date}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        },
    }).then(r => r.json());

export const createMetric = (data, token) =>
    fetch(`${BASE}/create_metric`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data),
    }).then(r => r.json());

export const updateMetric = (id, data, token) =>
    fetch(`${BASE}/${id}`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data),
    }).then(r => r.json());

export const deleteMetric = (id, token) =>
    fetch(`${BASE}/${id}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`
        },
    });
