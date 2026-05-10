const BASE = '/api/v1/extraction';

export const extractMetricsForUser = (userId, token) =>
    fetch(`${BASE}/run/${userId}`,
        {method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
    }}).then(r => {
        if (r.status === 401) throw new Error('Unauthorized');
        return r.json();
    });