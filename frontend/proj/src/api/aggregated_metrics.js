const BASE = '/api/v1/metrics';

/**
 * Get average metrics from the organization to display
 * the aggregated organization metrics
 *
 * @param source source of the metrics
 * @param token authorization token
 *
 * @returns {Promise<any>}
 */
export const getAggAverages = (token, source) => {
    const params = new URLSearchParams();
    if (source && source !== "null") {
        params.append('source', source);
    }
    return fetch(`${BASE}/averages?${params}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    }).then(res => res.ok ? res.json() : Promise.reject('Failed to load averages'));
};