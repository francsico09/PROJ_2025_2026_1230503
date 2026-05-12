const BASE = '/api/v1/users';

export const fetchUsers = (token,
                         {
                             page = 1,
                             pageSize = 20,
                             search = '',
                             sortBy = 'name',
                             sortDir = 'asc' } = {}
) => {
    const params = new URLSearchParams(
        {
        page, page_size:
        pageSize,
        search,
        sort_by: sortBy,
        sort_dir: sortDir
    });

    return fetch(`/api/v1/users/?${params}`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    }
    ).then(async r => {
        if (!r.ok) throw new Error((await r.json()).detail || 'Failed');
        return r.json();
    });
};

export const createUser = (data, token) =>
    fetch(`${BASE}/`, {
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