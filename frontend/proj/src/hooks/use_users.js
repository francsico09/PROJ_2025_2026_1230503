import { useState, useEffect, useCallback } from 'react';
import { getUsers, updateUser, deleteUser, createUser } from '../api/users.js';

export function useUsers() {
    const [users, setUsers]     = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError]     = useState(null);

    const token = localStorage.getItem('token');

    const fetchUsers = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const data = await getUsers(token);
            setUsers(data);

        } catch (e) {
            setError('Couldn\'t load users');

        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchUsers(); }, [fetchUsers]);

    const create = async (data) => {
        const created = await createUser(data, token);
        setUsers(prev => [...prev, created]);

        return created;
    };

    const update = async (id, data) => {
        const updated = await updateUser(id, data, token);
        setUsers(prev => prev.map(u => u.id === id ? updated : u));

        return updated;
    };

    const remove = async (id) => {
        await deleteUser(id, token);
        setUsers(prev => prev.filter(u => u.id !== id));
    };

    return {
        users,
        loading,
        error,
        create,
        update,
        remove,
        refresh: fetchUsers
    };
}