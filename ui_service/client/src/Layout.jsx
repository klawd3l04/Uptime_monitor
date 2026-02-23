import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from './AuthContext';

const Layout = ({ stats }) => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const getActiveTab = () => {
        if (location.pathname === '/') return 'dashboard';
        if (location.pathname.startsWith('/monitor/')) return 'monitor details';
        if (location.pathname === '/incidents') return 'incidents';
        if (location.pathname === '/settings') return 'settings';
        return '';
    };

    const activeTab = getActiveTab();

    return (
        <div className="layout">
            <aside className="sidebar">
                <div className="sidebar-logo">
                    <span>Uptime Monitor</span>
                </div>
                <nav>
                    <button className={activeTab === 'dashboard' ? 'active' : ''} onClick={() => navigate('/')}>
                        <span className="icon">📊</span> Dashboard
                    </button>
                    <button className={activeTab === 'incidents' ? 'active' : ''} onClick={() => navigate('/incidents')}>
                        <span className="icon">🚨</span> Incidents
                    </button>
                    <button className={activeTab === 'settings' ? 'active' : ''} onClick={() => navigate('/settings')}>
                        <span className="icon">⚙️</span> Settings
                    </button>
                </nav>

                <div className="sidebar-user">
                    <div className="user-info">
                        <div className="user-avatar">{user.username.charAt(0).toUpperCase()}</div>
                        <span className="user-name">{user.username}</span>
                    </div>
                    <button className="btn-logout" onClick={logout}>Logout</button>
                </div>

                <div className="sidebar-footer">
                    <span className="version">v1.4.0</span>
                </div>
            </aside>

            <main className="main-content">
                <header className="top-bar">
                    <div className="page-info">
                        <h2>{activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}</h2>
                        <p>Real-time system monitoring</p>
                    </div>
                    {stats && (
                        <div className="global-stats">
                            <div className="stat-pill">
                                <span className="label">Total</span>
                                <span className="value">{stats.total}</span>
                            </div>
                            <div className="stat-pill up">
                                <span className="label">Online</span>
                                <span className="value">{stats.up}</span>
                            </div>
                            <div className="stat-pill down">
                                <span className="label">Offline</span>
                                <span className="value">{stats.down}</span>
                            </div>
                        </div>
                    )}
                </header>
                <div className="content-area">
                    <Outlet />
                </div>
            </main>
        </div>
    );
};

export default Layout;
