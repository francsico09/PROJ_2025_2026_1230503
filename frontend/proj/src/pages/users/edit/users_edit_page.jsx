import { useState } from 'react';
import { useUsers } from '../../../hooks/use_users.js';
import UserEditView from './user_edit_view.jsx';

const EMPTY_FORM = {
    name: '',
    email: '',
    role: 'researcher',
    active: true,
    password: '',
};

export default function UserEditPage({ item, onBack }) {
    const isNew = !item;

    const [form, setForm] = useState(item ? {
        id: item.user_id,
        name: item.name,
        email: item.email,
        role: item.role,
        active: item.active,
    } : EMPTY_FORM);

    const [saving, setSaving] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState(null);

    const { create, update } = useUsers();

    const handleChange = (key, value) => {
        setSuccess(false);
        setError(null);
        setForm(prev => ({ ...prev, [key]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError(null);
        setSuccess(false);

        try {
            if (isNew) {
                await create(form);
            } else {
                const payload = { ...form };
                if (!payload.password) delete payload.password;
                await update(item.id, payload);
            }

            setSuccess(true);
            if (isNew) onBack();
        } catch {
            setError('Something went wrong. Please try again.');
        } finally {
            setSaving(false);
        }
    };

    return (
        <UserEditView
            isNew={isNew}
            item={item}
            form={form}
            saving={saving}
            success={success}
            error={error}
            onBack={onBack}
            onChange={handleChange}
            onSubmit={handleSubmit}
        />
    );
}