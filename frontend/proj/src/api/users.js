const BASE = '/api/v1/users';

export const getUsers = (token) =>
    fetch(`${BASE}/`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        }
        ).then(r => r.json());

export const createUser = (data, token) =>
    fetch(`${BASE}/create_user`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data),
    }).then(r => r.json());

export const updateUser = (id, data, token) =>
    fetch(`${BASE}/${id}`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data),
    }).then(r => r.json());

export const deleteUser = (id, token) =>
    fetch(`${BASE}/${id}`, {
        method: 'DELETE' ,
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });