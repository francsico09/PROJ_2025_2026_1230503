import { useState } from 'react';
import MetricEditView from './metrics_edit_view.jsx';

export default function MetricEditFromUserPage({ metric, user, onBack }) {
    const [form, setForm] = useState({
        h_index: metric.h_index,
        i10_index: metric.i10_index,
        total_citations: metric.total_citations,
        total_publications: metric.total_publications,
    });

    const [saving, setSaving] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState(null);

    const handleChange = (key, value) => {
        setSuccess(false);
        setError(null);
        setForm(prev => ({ ...prev, [key]: Number(value) }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError(null);
        setSuccess(false);

        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`/api/v1/researcher_metrics/${metric.id}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(form),
            });

            if (!response.ok) {
                throw new Error('Failed to update metric');
            }

            setSuccess(true);
            setTimeout(onBack, 1500);
        } catch {
            setError('Something went wrong. Please try again.');
        } finally {
            setSaving(false);
        }
    };

    return (
        <MetricEditView
            item={metric}
            user={user}
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

