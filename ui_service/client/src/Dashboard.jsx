import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { AreaChart, Area, ResponsiveContainer } from 'recharts'
import { useAuth } from './AuthContext'

const API_BASE = '/api'

const Modal = ({ isOpen, onClose, onConfirm, title, message }) => {
    if (!isOpen) return null;
    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <h3>{title}</h3>
                <p>{message}</p>
                <div className="modal-actions">
                    <button className="btn-secondary" onClick={onClose}>Cancel</button>
                    <button className="btn-danger" onClick={onConfirm}>Confirm Delete</button>
                </div>
            </div>
        </div>
    );
};

function Dashboard({ setGlobalStats }) {
    const { token, logout } = useAuth();
    const navigate = useNavigate();
    const [monitors, setMonitors] = useState([])
    const [statuses, setStatuses] = useState({})
    const [histories, setHistories] = useState({})
    const [newUrl, setNewUrl] = useState('')
    const [loading, setLoading] = useState(false)
    const [showModal, setShowModal] = useState(false)
    const [targetId, setTargetId] = useState(null)

    const api = axios.create({
        baseURL: API_BASE,
        headers: token ? { Authorization: `Bearer ${token}` } : {}
    });

    const fetchMonitors = useCallback(async () => {
        try {
            const res = await api.get('/monitors')
            setMonitors(res.data)
        } catch (err) {
            console.error('Fetch error:', err)
            if (err.response?.status === 401) logout();
        }
    }, [logout]);

    const updateStatuses = useCallback(async () => {
        if (monitors.length === 0) return;
        const newStatuses = { ...statuses }
        const newHistories = { ...histories }

        for (const m of monitors) {
            try {
                const [statusRes, historyRes] = await Promise.all([
                    api.get(`/status/${m.id}`),
                    api.get(`/history/${m.id}`)
                ])

                if (statusRes.data) newStatuses[m.id] = statusRes.data
                if (historyRes.data) newHistories[m.id] = historyRes.data
            } catch (err) {
                console.warn(`Error updating monitor ${m.id}:`, err)
            }
        }
        setStatuses(newStatuses)
        setHistories(newHistories)
    }, [monitors, statuses, histories]);

    useEffect(() => {
        fetchMonitors()
    }, [fetchMonitors])

    useEffect(() => {
        if (monitors.length > 0) {
            updateStatuses()
            const interval = setInterval(updateStatuses, 5000)
            return () => clearInterval(interval)
        }
    }, [monitors, updateStatuses])

    // Update global status summary for the layout
    useEffect(() => {
        const stats = {
            total: monitors.length,
            up: Object.values(statuses).filter(s => s.is_up).length,
            down: Object.values(statuses).filter(s => s.is_up === false).length
        }
        setGlobalStats(stats)
    }, [monitors, statuses, setGlobalStats])

    const normalizeUrl = (url) => {
        if (!url) return "";
        let trimmed = url.trim();
        if (!trimmed) return "";
        if (/^https?:\/\//i.test(trimmed)) return trimmed;
        return `https://${trimmed}`;
    };

    const addMonitor = async (e) => {
        e.preventDefault()
        if (!newUrl) return
        setLoading(true)
        const normalized = normalizeUrl(newUrl);
        try {
            await api.post('/monitors', { url: normalized, interval_seconds: 60 })
            setNewUrl('')
            fetchMonitors()
        } catch (err) {
            alert('Failed to add monitor')
        }
        setLoading(false)
    }

    const handleDeleteClick = (e, id) => {
        e.stopPropagation();
        setTargetId(id)
        setShowModal(true)
    }

    const confirmDelete = async () => {
        try {
            await api.delete(`/monitors/${targetId}`)
            setShowModal(false)
            fetchMonitors()
        } catch (err) {
            alert('Failed to delete monitor')
        }
    }

    return (
        <div className="content-inner">
            <form className="add-monitor-form" onSubmit={addMonitor}>
                <input
                    type="text"
                    placeholder="Add site (e.g. google.com)"
                    value={newUrl}
                    onChange={(e) => setNewUrl(e.target.value)}
                    onBlur={() => setNewUrl(prev => normalizeUrl(prev))}
                    onKeyDown={(e) => { if (e.key === 'Enter') setNewUrl(prev => normalizeUrl(prev)) }}
                    required
                />
                <button type="submit" disabled={loading} className="btn-primary">
                    {loading ? 'Adding...' : '+ Add Monitor'}
                </button>
            </form>

            <div className="monitor-grid">
                {monitors.length === 0 && <p className="empty-state">No monitors registered.</p>}
                {monitors.map(m => {
                    const status = statuses[m.id]
                    const history = histories[m.id] || []
                    const isUp = status ? status.is_up : null
                    let domain = ""
                    try { domain = new URL(m.url).hostname } catch (e) { domain = m.url }
                    const faviconUrl = `https://www.google.com/s2/favicons?domain=${domain}&sz=64`

                    return (
                        <div key={m.id} className="monitor-card clickable" onClick={() => navigate(`/monitor/${m.id}`)}>
                            <div className="monitor-header">
                                <div className="monitor-main">
                                    <div className="favicon-box">
                                        <img src={faviconUrl} alt="" onError={(e) => { e.target.style.display = 'none' }} />
                                    </div>
                                    <div className="meta-info">
                                        <span className="url-text">{m.url}</span>
                                        <span className="refresh-rate">Checks every {m.interval_seconds}s</span>
                                    </div>
                                </div>
                                <div className="monitor-actions">
                                    <div className="status-group">
                                        {status && <span className="latency-text">{status.latency_ms}ms</span>}
                                        <span className={`status-dot ${isUp === true ? 'up' : isUp === false ? 'down' : 'pending'}`}>
                                            {isUp === true ? 'Online' : isUp === false ? 'Offline' : '...'}
                                        </span>
                                    </div>
                                    <button type="button" className="delete-icon-btn" onClick={(e) => handleDeleteClick(e, m.id)}>×</button>
                                </div>
                            </div>
                            <div className="chart-wrapper">
                                <ResponsiveContainer width="100%" height={100}>
                                    <AreaChart data={history}>
                                        <defs>
                                            <linearGradient id={`grad-${m.id}`} x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <Area type="monotone" dataKey="latency_ms" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill={`url(#grad-${m.id})`} isAnimationActive={false} />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    )
                })}
            </div>

            <Modal isOpen={showModal} onClose={() => setShowModal(false)} onConfirm={confirmDelete} title="Delete Monitor" message="Are you sure you want to remove this monitor?" />
        </div>
    )
}

export default Dashboard;
