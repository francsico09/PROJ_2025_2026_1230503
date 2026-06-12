import {useState, useEffect, useCallback, useRef} from 'react';
import {updateUser, deleteUser, createUser, fetchUsers} from '../api/users.js';

/**
 * A custom hook to manage users, including fetching with pagination and search,
 * as well as creating, updating, and deleting users.
 *
 * @param initialPageSize
 * @param exclude_names
 * @returns {{users: *[], total: number, pages: number, page: number, pageSize: number, search: string, loading: boolean, error: unknown, setPage: (value: (((prevState: number) => number) | number)) => void, setSearch: handleSearch, create: function(*): Promise<unknown>, update: function(*, *): Promise<unknown>, remove: (function(*): Promise<void>)|*, refresh: (function(): Promise<void>)|*}}
 */
export function useUsers({initialPageSize = 20, exclude_names = [] } = {}) {
    const [items, setItems] = useState([]);
    const [total, setTotal] = useState(0);
    const [pages, setPages] = useState(0);
    const [page, setPage] = useState(1);
    const [pageSize] = useState(initialPageSize);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const token = useRef(localStorage.getItem('token'));
    const excludeRef = useRef(exclude_names);

    const fetch = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const data = await fetchUsers(token.current,
                {
                    page,
                    pageSize,
                    search,
                    exclude_names: excludeRef.current,
                });
            setItems(data.items);
            setTotal(data.total);
            setPages(data.pages);

        } catch {
            setError('Failed to load users.');
            setItems([]);
        } finally {
            setLoading(false);
        }
    }, [page, pageSize, search]);

    useEffect(() => {
        fetch();
    }, [fetch]);

    const handleSearch = (val) => {
        setSearch(val);
        setPage(1);
    };

    const create = async (data) => {
        const created = await createUser(data, token.current);
        setItems(prev => [...prev, created]);

        return created;
    };

    const update = async (id, data) => {
        const updated = await updateUser(id, data, token.current);
        setItems(prev => prev.map(u => u.id === id ? updated : u));

        return updated;
    };

    const remove = async (id) => {
        await deleteUser(id, token.current);
        setItems(prev => prev.filter(u => u.id !== id));
    };

    return {
        users: items, total, pages, page, pageSize,
        search, loading, error,
        setPage,
        setSearch: handleSearch,
        create,
        update,
        remove,
        refresh: fetch,
    };
}