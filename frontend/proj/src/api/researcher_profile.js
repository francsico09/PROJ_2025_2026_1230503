const BASE = '/api/v1/researcher_profiles';

export const getProfiles = (token) =>
    fetch(`${BASE}/`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    }).then(r => r.json());

export const getProfileById = (id, token) =>
    fetch(`${BASE}/${id}`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    }).then(r => r.json());

export const updateProfile = (id, data, token) =>
    fetch(`${BASE}/${id}`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json' ,
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data),
    }).then(r => r.json());

export const createProfile = (data, token) =>
    fetch(`${BASE}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data),
    }).then(r => r.json());

export const deleteProfile = (id, token) =>
    fetch(`${BASE}/${id}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`
        },
    }).then(r => r.json());
