import Icon, { ICONS } from '../../../components/icon.jsx';

export default function UserEditView({
                                         isNew,
                                         item,
                                         form,
                                         saving,
                                         success,
                                         error,
                                         onBack,
                                         onChange,
                                         onSubmit
                                     }) {
    return (
        <div>
            <button className="back-btn" onClick={onBack}>
                <Icon d={ICONS.back} size={13} />
                Back to users
            </button>

            <div className="page-header">
                <h2>{isNew ? 'Create user' : 'Edit user'}</h2>
                <p>{isNew ? 'Add a new user to the system.' : `Editing ${item.name}`}</p>
            </div>

            <form className="edit-card" onSubmit={onSubmit}>
                <div className="edit-card-title">
                    User information
                </div>

                <div className="form-row">
                    <div className="form-group">
                        <label>Full name</label>
                        <input
                            className="form-input"
                            type="text"
                            placeholder="John Doe"
                            value={form.name}
                            onChange={e => onChange('name', e.target.value)}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label>Email address</label>
                        <input
                            className="form-input"
                            type="email"
                            placeholder="john.doe@institution.pt"
                            value={form.email}
                            onChange={e => onChange('email', e.target.value)}
                            required
                        />
                    </div>
                </div>

                <div className="form-row">
                    <div className="form-group">
                        <label>Role</label>
                        <select
                            className="form-select"
                            value={form.role}
                            onChange={e => onChange('role', e.target.value)}
                        >
                            <option value="researcher">researcher</option>
                            <option value="admin">admin</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label>Status</label>
                        <select
                            className="form-select"
                            value={form.active ? 'true' : 'false'}
                            onChange={e => onChange('active', e.target.value === 'true')}
                        >
                            <option value="true">Active</option>
                            <option value="false">Inactive</option>
                        </select>
                    </div>
                </div>

                <div className="form-group">
                    <label>
                        Password
                        {!isNew && <span className="hint"> — leave blank to keep current</span>}
                    </label>
                    <input
                        className="form-input"
                        type="password"
                        placeholder={isNew ? 'Minimum 8 characters' : '••••••••'}
                        value={form.password ?? ''}
                        onChange={e => onChange('password', e.target.value)}
                        required={isNew}
                        minLength={isNew ? 8 : undefined}
                    />
                </div>

                {success && (
                    <div className="alert alert-success">
                        <Icon d={ICONS.check} size={14} />
                        {isNew ? 'User created successfully.' : 'Changes saved successfully.'}
                    </div>
                )}

                {error && (
                    <div className="alert alert-danger">
                        {error}
                    </div>
                )}

                <div className="form-actions">
                    <button
                        type="submit"
                        className="btn btn-primary"
                        disabled={saving}
                    >
                        {saving && <span className="spinner" />}
                        {saving ? 'Saving…' : isNew ? 'Create user' : 'Save changes'}
                    </button>

                    <button
                        type="button"
                        className="btn btn-outline"
                        onClick={onBack}
                        disabled={saving}
                    >
                        Cancel
                    </button>
                </div>
            </form>
        </div>
    );
}