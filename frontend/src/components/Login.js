import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../api';

function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const response = await api.post('/login', {
                username: email,
                password: password
            });
            localStorage.setItem('token', response.data.access_token);
            navigate('/chat');
        } catch (error) {
            setError(error.response?.data?.detail || "Login failed. Please try again.");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div style={{ maxWidth: '300px', margin: '0 auto', padding: '20px' }}>
            <h2>Login</h2>
            <form onSubmit={handleLogin}>
                <input
                    type="email"
                    placeholder="Email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    required
                    style={{ width: '100%', marginBottom: '10px', padding: '5px' }}
                />
                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                    style={{ width: '100%', marginBottom: '10px', padding: '5px' }}
                />
                <button type="submit" disabled={loading} style={{ width: '100%', padding: '5px' }}>
                    {loading ? 'Logging in...' : 'Login'}
                </button>
            </form>
            {error && <p style={{ color: 'red' }}>{error}</p>}
            <p>Don't have an account? <Link to="/register">Register</Link></p>
        </div>
    );
}

export default Login;
