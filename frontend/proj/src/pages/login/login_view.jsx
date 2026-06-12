/**
 * Login view component.
 *
 * @param email
 * @param password
 * @param loading
 * @param error
 * @param onEmailChange
 * @param onPasswordChange
 * @param onSubmit
 * @returns {React.JSX.Element}
 * @constructor
 */
export default function LoginView({
                                      email,
                                      password,
                                      loading,
                                      error,
                                      onEmailChange,
                                      onPasswordChange,
                                      onSubmit
                                  }) {
    return (
        <div className="login-wrap">
            <div className="login-left">
                <h1 className="login-heading">
                    Research<br />Analytics and<br />Metrics<br />Platform
                </h1>
                <p className="login-sub">
                    Centralise and monitor researcher metrics from
                    Google Scholar, Web of Science, Scopus and ORCID.
                </p>
                <div className="login-dots">
                    <span className="dot dot-active" />
                    <span className="dot" />
                    <span className="dot" />
                </div>
            </div>

            <div className="login-right">
                <form className="login-card" onSubmit={onSubmit}>
                    <h2 className="login-card-title">Sign in</h2>
                    <p className="login-card-sub">
                        Use your ISEP institutional credentials.
                    </p>

                    <div className="form-group">
                        <label>Email address</label>
                        <input
                            className="form-input"
                            type="email"
                            value={email}
                            onChange={e => onEmailChange(e.target.value)}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label>Password</label>
                        <input
                            className="form-input"
                            type="password"
                            value={password}
                            onChange={e => onPasswordChange(e.target.value)}
                            required
                        />
                    </div>

                    {error && (
                        <div className="alert alert-danger">
                            {error}
                        </div>
                    )}

                    <button type="submit" className="login-btn" disabled={loading}>
                        {loading ? 'Signing in…' : 'Sign in'}
                    </button>
                </form>
            </div>
        </div>
    );
}