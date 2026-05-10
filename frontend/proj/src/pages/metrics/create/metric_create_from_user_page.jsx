import { useState } from 'react';
import { useResearcherMetrics } from '../../../hooks/use_researcher_metrics.js';
import MetricCreateView from './metrics_create_view.jsx';

const EMPTY_FORM = {
    h_index: '',
    i10_index: '',
    total_citations: '',
    total_publications: '',
    source_name: 'scholar',
    source_url: '',
};

export default function MetricCreateFromUserPage({ user, onBack }) {
    const [form, setForm] = useState(EMPTY_FORM);
    const [saving, setSaving] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState(null);

    const { create } = useResearcherMetrics(user.id);

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
            await create({
                researcher_id: user.id,
                h_index: Number(form.h_index),
                i10_index: Number(form.i10_index),
                total_citations: Number(form.total_citations),
                total_publications: Number(form.total_publications),
                source: {
                    name: form.source_name,
                    url: form.source_url,
                },
            });

            setSuccess(true);
            setTimeout(onBack, 1500);
        } catch (err) {
            setError(err.message || 'Something went wrong.');
        } finally {
            setSaving(false);
        }
    };

    return (
        <MetricCreateView
            form={{ ...form, researcher_id: user.id }}
            researchers={[user]}
            loadingUsers={false}
            saving={saving}
            success={success}
            error={error}
            onBack={onBack}
            onChange={handleChange}
            onSubmit={handleSubmit}
        />
    );
}


