import { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';

const API_BASE = '/api';

const Settings = () => {
    const { token, logout, user: authUser } = useAuth();
    const [activeTab, setActiveTab] = useState('profile');
    const [profile, setProfile] = useState({
        username: '',
        email: '',
        notification_email: '',
        slack_webhook_url: ''
    });
    const [passwords, setPasswords] = useState({
        current: '',
        new: '',
        confirm: ''
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState({ text: '', type: '' });

    const api = axios.create({
        baseURL: API_BASE,
        headers: token ? { Authorization: `Bearer ${token}` } : {}
    });

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                const res = await api.get('/profile');
                setProfile(res.data);
            } catch (err) {
                console.error('Failed to fetch profile:', err);
                if (err.response?.status === 401) logout();
            } finally {
                setLoading(false);
            }
        };
        fetchProfile();
    }, [logout]);

    const handleUpdate = async (e) => {
        e.preventDefault();
        setSaving(true);
        setMessage({ text: '', type: '' });
        try {
            const data = activeTab === 'profile' ? {
                email: profile.email
            } : activeTab === 'notifications' ? {
                notification_email: profile.notification_email,
                slack_webhook_url: profile.slack_webhook_url
            } : {
                password: passwords.new
            };

            await api.put('/profile', data);
            setMessage({ text: 'Settings updated successfully!', type: 'success' });
            if (activeTab === 'security') setPasswords({ current: '', new: '', confirm: '' });
        } catch (err) {
            setMessage({ text: err.response?.data?.error || 'Update failed', type: 'error' });
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="loading-screen">Loading premium settings...</div>;

    const tabs = [
        { id: 'profile', label: 'General Profile', icon: '👤', title: 'Profile Information', desc: 'Update your account identity and contact details.' },
        { id: 'notifications', label: 'Alert Channels', icon: '🔔', title: 'Notification Channels', desc: 'Configure how and where you receive uptime alerts.' },
        { id: 'security', label: 'Security', icon: '🔒', title: 'Security & Password', desc: 'Manage your authentication and keep your account safe.' }
    ];

    const currentTab = tabs.find(t => t.id === activeTab);

    return (
        <div className="settings-page">
            <div className="settings-container">
                <header className="settings-nav-header">
                    <div className="page-info">
                        <h2>Workplace Settings</h2>
                        <p>Configure your personal profile and notification preferences</p>
                    </div>
                </header>

                <div className="settings-tabs">
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            className={`settings-tab-btn ${activeTab === tab.id ? 'active' : ''}`}
                            onClick={() => { setActiveTab(tab.id); setMessage({ text: '', type: '' }); }}
                        >
                            <span>{tab.icon}</span> {tab.label}
                        </button>
                    ))}
                </div>

                {message.text && (
                    <div className={`status-alert ${message.type}`}>
                        {message.type === 'success' ? '✅' : '❌'} {message.text}
                    </div>
                )}

                <div className="settings-content-grid">
                    <aside className="settings-sidebar-info">
                        <h2>{currentTab.title}</h2>
                        <p>{currentTab.desc}</p>
                    </aside>

                    <main className="settings-section-card glass">
                        <form onSubmit={handleUpdate} className="settings-form">
                            {activeTab === 'profile' && (
                                <>
                                    <div className="premium-form-group">
                                        <label>Username</label>
                                        <div className="premium-input-box">
                                            <input type="text" value={profile.username} disabled className="disabled-input" />
                                        </div>
                                        <span className="input-hint">Unique identifier used for your account</span>
                                    </div>
                                    <div className="premium-form-group">
                                        <label>Primary Email</label>
                                        <div className="premium-input-box">
                                            <input
                                                type="email"
                                                value={profile.email}
                                                onChange={e => setProfile({ ...profile, email: e.target.value })}
                                                required
                                            />
                                        </div>
                                    </div>
                                </>
                            )}

                            {activeTab === 'notifications' && (
                                <>
                                    <div className="premium-form-group">
                                        <label>Emergency Alert Email</label>
                                        <div className="premium-input-box">
                                            <input
                                                type="email"
                                                placeholder="alerts@domain.com"
                                                value={profile.notification_email}
                                                onChange={e => setProfile({ ...profile, notification_email: e.target.value })}
                                            />
                                        </div>
                                        <span className="input-hint">Used solely for incident reports (optional)</span>
                                    </div>
                                    <div className="premium-form-group">
                                        <label>Slack Webhook URL</label>
                                        <div className="premium-input-box">
                                            <input
                                                type="url"
                                                placeholder="https://hooks.slack.com/services/..."
                                                value={profile.slack_webhook_url}
                                                onChange={e => setProfile({ ...profile, slack_webhook_url: e.target.value })}
                                            />
                                        </div>
                                        <span className="input-hint">Get instant push notifications in your Slack channels</span>
                                    </div>
                                </>
                            )}

                            {activeTab === 'security' && (
                                <>
                                    <div className="premium-form-group">
                                        <label>New Password</label>
                                        <div className="premium-input-box">
                                            <input
                                                type="password"
                                                placeholder="Enter a strong password"
                                                value={passwords.new}
                                                onChange={e => setPasswords({ ...passwords, new: e.target.value })}
                                                required
                                            />
                                        </div>
                                    </div>
                                    <div className="premium-form-group">
                                        <label>Confirm Password</label>
                                        <div className="premium-input-box">
                                            <input
                                                type="password"
                                                placeholder="Repeat your new password"
                                                value={passwords.confirm}
                                                onChange={e => setPasswords({ ...passwords, confirm: e.target.value })}
                                                required
                                            />
                                        </div>
                                    </div>
                                </>
                            )}

                            <div className="settings-footer">
                                <button type="submit" disabled={saving} className="btn-premium-save">
                                    {saving ? 'Saving Changes...' : 'Save Settings'}
                                </button>
                            </div>
                        </form>
                    </main>
                </div>
            </div>
        </div>
    );
};

export default Settings;
