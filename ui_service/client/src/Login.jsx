import { useState } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';

const Login = () => {
    const [isLogin, setIsLogin] = useState(true);
    const [formData, setFormData] = useState({ username: '', email: '', password: '' });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        const endpoint = isLogin ? '/api/login' : '/api/register';

        try {
            const res = await axios.post(endpoint, formData);
            if (isLogin) {
                login(res.data);
            } else {
                alert('Registered successfully! Now please login.');
                setIsLogin(true);
            }
        } catch (err) {
            setError(err.response?.data?.error || 'Something went wrong');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-background">
                <div className="blob blob-1"></div>
                <div className="blob blob-2"></div>
                <div className="blob blob-3"></div>
            </div>

            <div className="auth-container">
                <div className="auth-card glass">
                    <div className="auth-header">
                        <div className="auth-badge">Security Layer</div>
                        <h1>Uptime Monitor</h1>
                        <p>{isLogin ? 'Sign in to access your dashboard' : 'Join the uptime monitoring network'}</p>
                    </div>

                    <form onSubmit={handleSubmit} className="auth-form">
                        {!isLogin && (
                            <div className="form-group">
                                <label>Email</label>
                                <div className="input-wrapper">
                                    <span className="input-icon">✉️</span>
                                    <input
                                        type="email"
                                        placeholder="email@example.com"
                                        value={formData.email}
                                        onChange={e => setFormData({ ...formData, email: e.target.value })}
                                        required
                                    />
                                </div>
                            </div>
                        )}
                        <div className="form-group">
                            <label>Username</label>
                            <div className="input-wrapper">
                                <span className="input-icon">👤</span>
                                <input
                                    type="text"
                                    placeholder="johndoe"
                                    value={formData.username}
                                    onChange={e => setFormData({ ...formData, username: e.target.value })}
                                    required
                                />
                            </div>
                        </div>
                        <div className="form-group">
                            <label>Password</label>
                            <div className="input-wrapper">
                                <span className="input-icon">🔒</span>
                                <input
                                    type="password"
                                    placeholder="••••••••"
                                    value={formData.password}
                                    onChange={e => setFormData({ ...formData, password: e.target.value })}
                                    required
                                />
                            </div>
                        </div>

                        {error && <div className="auth-error-v2">{error}</div>}

                        <button type="submit" className="auth-submit-btn" disabled={loading}>
                            {loading ? (
                                <span className="loader-alt"></span>
                            ) : (
                                <>{isLogin ? 'Secure Sign In' : 'Create Secure Account'}</>
                            )}
                        </button>
                    </form>

                    <div className="auth-footer-v2">
                        <span>{isLogin ? "New here?" : "Joined before?"}</span>
                        <button onClick={() => setIsLogin(!isLogin)} className="toggle-btn">
                            {isLogin ? "Create Account" : "Sign In to Dashboard"}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;
