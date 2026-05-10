import { useEffect, useState } from 'react';
import Icon, { ICONS } from '../../components/icon.jsx';
import { extractMetricsForUser } from '../../api/extraction.js';
import {useProfiles} from "../../hooks/use_profiles.js";

const EMPTY_FORM = {
    orcid: '',
    scholar_id: '',
    wos_id: '',
    scopus_id: '',
    affiliation: '',
    biography: '',
    keywords: []
};

export default function ProfileFormPage({ user, profile, onBack, onExtraction }) {
    const isEdit = !!profile;

    const [form, setForm] = useState(EMPTY_FORM);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(false);
    const [extractionLoading, setExtractionLoading] = useState(false);
    const { update, create } = useProfiles();

    useEffect(() => {
        if (profile) {
            setForm({
                orcid: profile.orcid ?? '',
                scholar_id: profile.scholar_id ?? '',
                wos_id: profile.wos_id ?? '',
                scopus_id: profile.scopus_id ?? '',
                affiliation: profile.affiliation ?? '',
                biography: profile.biography ?? '',
                keywords: profile.keywords ?? []
            });
        }
    }, [profile]);

    const set = (key, value) => {
        setForm(prev => ({ ...prev, [key]: value }));
        setError(null);
        setSuccess(false);
    };

    const handleExtraction = async () => {
        setExtractionLoading(true);
        setError(null);

        try {
            const token = localStorage.getItem('token');
            const result = await extractMetricsForUser(user.id, token);

            console.log('Extraction result:', result);

            setSuccess(true);

            if (onExtraction) {
                onExtraction(result);
            }

        } catch (err) {
            setError('Error extracting metrics.');
        } finally {
            setExtractionLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        setLoading(true);
        setError(null);
        setSuccess(false);

        try {
            const payload = {
                orcid: form.orcid,
                scholar_id: form.scholar_id,
                wos_id: form.wos_id,
                scopus_id: form.scopus_id,
                affiliation: form.affiliation,
                biography: form.biography,
                keywords: form.keywords ?? [],
                metrics: profile?.metrics ?? []
            };

            if (isEdit) {
                await update(profile.id, payload);
            } else {
                await create({
                    ...payload,
                    user_id: user.id
                });
            }

            setSuccess(true);
        } catch (err) {
            setError(err.message || 'Error saving profile.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            {/* BACK */}
            <button className="back-btn" onClick={onBack}>
                <Icon d={ICONS.back} size={13} />
                Back
            </button>

            {/* HEADER */}
            <div className="page-header">
                <h2>
                    {isEdit ? 'Edit profile' : 'Create profile'}
                </h2>
                <p>
                    {user?.name}
                </p>
            </div>

            {/* FORM */}
            <form className="edit-card" onSubmit={handleSubmit}>

                <div className="edit-card-title">
                    Researcher profile
                </div>

                {/* ORCID */}
                <div className="form-group">
                    <label>ORCID ID</label>
                    <input
                        className="form-input"
                        value={form.orcid}
                        onChange={(e) => set('orcid', e.target.value)}
                        placeholder="0000-0000-0000-0000"
                    />
                </div>

                {/* SCHOLAR */}
                <div className="form-group">
                    <label>Google Scholar ID</label>
                    <input
                        className="form-input"
                        value={form.scholar_id}
                        onChange={(e) => set('scholar_id', e.target.value)}
                        placeholder="TWGHJEYAAFAK"
                    />
                </div>

                {/* WOS ID */}
                <div className="form-group">
                    <label>Web of Science ID (ResearcherID)</label>
                    <input
                        className="form-input"
                        value={form.wos_id}
                        onChange={(e) => set('wos_id', e.target.value)}
                        placeholder="A-1234-2023"
                    />
                </div>

                {/* Scopus ID */}
                <div className="form-group">
                    <label>Scopus ID</label>
                    <input
                        className="form-input"
                        value={form.scopus_id}
                        onChange={(e) => set('scopus_id', e.target.value)}
                        placeholder="12345678987"
                    />
                </div>

                {/* AFFILIATION */}
                <div className="form-group">
                    <label>Institutional Affiliation</label>
                    <input
                        className="form-input"
                        value={form.affiliation}
                        onChange={(e) => set('affiliation', e.target.value)}
                        placeholder="e.g., Department of Computer Science, University Name"
                    />
                </div>

                {/* BIO */}
                <div className="form-group">
                    <label>Biography</label>
                    <textarea
                        className="form-input"
                        rows={5}
                        value={form.biography}
                        onChange={(e) => set('biography', e.target.value)}
                        placeholder="Short academic biography..."
                    />
                </div>

                <div className="form-group">
                    <label>Keywords</label>
                    <input
                        className="form-input"
                        placeholder="AI, Machine Learning, Networks..."
                        value={form.keywords.join(', ')}
                        onChange={(e) => {
                            const value = e.target.value;

                            const keywords = value
                                .split(',')
                                .map(k => k.trim())
                                .filter(k => k.length > 0);

                            set('keywords', keywords);
                        }}
                    />
                </div>

                {/* STATUS */}
                {success && (
                    <div className="alert alert-success">
                        Profile saved successfully.
                    </div>
                )}

                {error && (
                    <div className="alert alert-danger">
                        {error}
                    </div>
                )}

                {/* ACTIONS */}
                <div className="form-actions">
                    <button
                        type="submit"
                        className="btn btn-primary"
                        disabled={loading}
                    >
                        {loading ? 'Saving…' : (isEdit ? 'Save changes' : 'Create profile')}
                    </button>

                    <button
                        type="button"
                        className="btn btn-outline"
                        onClick={handleExtraction}
                        disabled={extractionLoading}
                    >
                        {extractionLoading ? 'Extracting…' : 'Extract metrics'}
                    </button>
                </div>
            </form>
        </div>
    );
}