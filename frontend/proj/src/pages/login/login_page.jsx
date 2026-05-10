import { useState } from 'react';
import { login } from '../../api/auth.js';
import LoginView from './login_view.jsx';

export default function LoginPage({ onLogin }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const data = await login(email, password);
            console.log('LOGIN RESPONSE:', data);
            if (!data.user_id) {
                console.log('User ID missing from server response');
            }

            const user = {
                id: data.user_id,
                name: data.user_name,
                email: data.user_email,
                role: data.user_role,
                initials: data.user_name
                    .split(' ')
                    .map(w => w[0])
                    .slice(0, 2)
                    .join('')
                    .toUpperCase(),
            };

            localStorage.removeItem('user');
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user', JSON.stringify(user));

            onLogin(user);

        } catch (err) {
            setError(err.message || 'Email or password is incorrect.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <LoginView
            email={email}
            password={password}
            loading={loading}
            error={error}
            onEmailChange={setEmail}
            onPasswordChange={setPassword}
            onSubmit={handleSubmit}
        />
    );
}