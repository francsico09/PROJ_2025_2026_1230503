const BASE = '/api/v1/export';

export const exportResearcherMetrics = async (researcherId, format, scope, token, dateParams = {}) => {
    const params = new URLSearchParams([
        ['format', format],
        ['scope', scope],
    ]);

    if (dateParams.startDate) {
        params.append('start_date', dateParams.startDate);
    }

    if (dateParams.endDate) {
        params.append('end_date', dateParams.endDate);
    }

    const url = `${BASE}/researcher_metric/${researcherId}?${params.toString()}`;

    const res = await fetch(url, {
        headers: {
            Authorization: `Bearer ${token}`
        },
    });

    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Export failed' }));
        throw new Error(err.detail || 'Export failed');
    }

    await _triggerDownload(res);
};

export const exportAllMetrics = async (format, scope, token, dateParams = {}) => {
    const params = new URLSearchParams([
        ['format', format],
        ['scope', scope],
    ]);

    if (dateParams.startDate) {
        params.append('start_date', dateParams.startDate);
    }

    if (dateParams.endDate) {
        params.append('end_date', dateParams.endDate);
    }

    const url = `${BASE}/researcher_metric?${params.toString()}`;

    const res = await fetch(url, {
        headers: {
            Authorization: `Bearer ${token}`
        },
    });

    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Export failed' }));
        throw new Error(err.detail || 'Export failed');
    }

    await _triggerDownload(res);
};

const _triggerDownload = async (res) => {
    const disposition = res.headers.get('Content-Disposition') || '';
    const match       = disposition.match(/filename="?([^"]+)"?/);
    const filename    = match ? match[1] : 'metrics_export';

    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);

    const a    = document.createElement('a');
    a.href     = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
};