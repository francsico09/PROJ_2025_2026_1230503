const BASE = '/api/v1/auth';

/**
 * Authenticates the user and returns the token with user data.
 *
 * @param {string} email
 * @param {string} password
 * @returns {Promise<{access_token, user_name, user_email, user_role}>}
 */
export const login = (email, password) =>
    fetch(`${BASE}/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password }),
    }).then(async r => {
        if (!r.ok) {
            const err = await r.json();
            throw new Error(err.detail || 'Login failed');
        }
        return r.json();
    });