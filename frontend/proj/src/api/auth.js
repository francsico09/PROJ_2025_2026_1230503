const BASE = '/api/v1/auth';

/**
 * Autentica o utilizador e devolve o token + dados do utilizador.
 * @param {string} email
 * @param {string} password
 * @returns {Promise<{access_token, user_name, user_email, user_role}>}
 */
export const login = (email, password) =>
    fetch(`${BASE}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
    }).then(async r => {
        if (!r.ok) {
            const err = await r.json();
            throw new Error(err.detail || 'Login failed');
        }
        return r.json();
    });

export const getMe = (token) =>
    fetch(`${BASE}/me`, {
        headers: { Authorization: `Bearer ${token}` },
    }).then(r => r.json());