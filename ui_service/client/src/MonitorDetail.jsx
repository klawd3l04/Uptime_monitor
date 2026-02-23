import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AreaChart, Area, ResponsiveContainer, YAxis, Tooltip, XAxis, CartesianGrid } from 'recharts';
import axios from 'axios';
import { useAuth } from './AuthContext';

const API_BASE = '/api';

const MonitorDetail = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const { token, logout } = useAuth();

    const [monitor, setMonitor] = useState(null);
    const [history, setHistory] = useState([]);
    const [incidents, setIncidents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const api = axios.create({
        baseURL: API_BASE,
        headers: token ? { Authorization: `Bearer ${token}` } : {}
    });

    const fetchData = useCallback(async () => {
        try {
            setLoading(true);
            const [monitorsRes, historyRes, incidentsRes] = await Promise.all([
                api.get('/monitors'),
                api.get(`/history/${id}`),
                api.get(`/monitors/${id}/incidents`)
            ]);

            const currentMonitor = monitorsRes.data.find(m => m.id === parseInt(id));
            if (!currentMonitor) throw new Error("Monitor not found");

            setMonitor(currentMonitor);
            setHistory(historyRes.data || []);
            setIncidents(incidentsRes.data || []);
            setError(null);
        } catch (err) {
            console.error('Fetch error:', err);
            setError(err.message || 'Failed to fetch details');
            if (err.response?.status === 401) logout();
        } finally {
            setLoading(false);
        }
    }, [id, logout]);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, [fetchData]);

    if (loading && !monitor) return <div className="loading-screen-inline">Analyzing Monitor...</div>;
    if (error) return (
        <div className="error-view">
            <h3>Monitor not found or error occurred</h3>
            <p>{error}</p>
            <button onClick={() => navigate('/')} className="btn-secondary">Back to Dashboard</button>
        </div>
    );

    const uptimePercent = history.length > 0
        ? ((history.filter(h => h.is_up).length / history.length) * 100).toFixed(2)
        : "100.00";

    return (
        <div className="detail-page-content">
            <header className="detail-header">
                <div className="header-left">
                    <button onClick={() => navigate('/')} className="back-btn">← Back to Dashboard</button>
                    <div className="monitor-title-group">
                        <h1>{monitor.url}</h1>
                        <span className={`status-badge ${history[0]?.is_up ? 'up' : 'down'}`}>
                            {history[0]?.is_up ? 'Online' : 'Offline'}
                        </span>
                    </div>
                </div>
                <div className="uptime-card">
                    <span className="uptime-label">30-Day Uptime</span>
                    <span className="uptime-value">{uptimePercent}%</span>
                </div>
            </header>

            <div className="detail-grid">
                <section className="analytics-section glass">
                    <div className="section-header">
                        <h3>Latency History (ms)</h3>
                        <span className="sub-text">Response times over time</span>
                    </div>
                    <div className="big-chart-wrapper">
                        <ResponsiveContainer width="100%" height={300}>
                            <AreaChart data={history}>
                                <defs>
                                    <linearGradient id="colorLatency" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                                <XAxis dataKey="timestamp" hide />
                                <YAxis stroke="rgba(255,255,255,0.4)" fontSize={12} tickFormatter={(val) => `${val}ms`} />
                                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#fff' }} itemStyle={{ color: '#3b82f6' }} />
                                <Area type="monotone" dataKey="latency_ms" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorLatency)" isAnimationActive={true} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </section>

                <section className="incidents-section glass">
                    <div className="section-header">
                        <h3>Incident Log</h3>
                        <span className="sub-text">Status changes</span>
                    </div>
                    <div className="incident-list">
                        {incidents.length === 0 ? (
                            <div className="empty-incidents">Stable. No incidents recorded.</div>
                        ) : (
                            incidents.map(incident => (
                                <div key={incident.id} className={`incident-item ${incident.event_type.toLowerCase()}`}>
                                    <div className="incident-mark"></div>
                                    <div className="incident-info">
                                        <div className="incident-top">
                                            <span className="event-type">{incident.event_type === 'DOWN' ? '🔴 Down' : '🟢 Up'}</span>
                                            <span className="incident-time">{new Date(incident.timestamp).toLocaleString()}</span>
                                        </div>
                                        <p className="incident-details">{incident.details || 'N/A'}</p>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </section>
            </div>
        </div>
    );
};

export default MonitorDetail;
