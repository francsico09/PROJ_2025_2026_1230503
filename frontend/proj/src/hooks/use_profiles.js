import { useState, useEffect, useCallback } from 'react';
import { getProfiles, getProfileById, updateProfile, createProfile, deleteProfile} from '../api/researcher_profile.js';

/**
 * A custom hook to manage researcher profiles, including fetching,
 * creating, updating, and deleting profiles.
 *
 * @returns {{profiles: *[], loading: boolean, error: unknown, create: function(*): Promise<unknown>, update: function(*, *): Promise<unknown>, remove: (function(*): Promise<void>)|*, refresh: (function(): Promise<void>)|*}}
 */
export function useProfiles() {
    const [profiles, setProfiles]     = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError]     = useState(null);
    const token = localStorage.getItem('token');

    const fetchProfiles = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await getProfiles();
            setProfiles(Array.isArray(data) ? data : data.data ?? []);
        } catch (e) {
            setError('Couldn\'t load researcher profiles.');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchProfiles(); }, [fetchProfiles]);

    const create = async (data) => {
        const created = await createProfile(data, token);
        setProfiles(prev => [...prev, created]);
        return created;
    };

    const update = async (id, data) => {
        const updated = await updateProfile(id, data, token);
        setProfiles(prev => prev.map(u => u.id === id ? updated : u));
        return updated;
    };

    const remove = async (id) => {
        await deleteProfile(id, token);
        setProfiles(prev => prev.filter(u => u.id !== id));
    };

    return { profiles, loading, error, create, update, remove, refresh: fetchProfiles };
}