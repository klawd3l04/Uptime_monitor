import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import Login from './Login';
import Layout from './Layout';
import Dashboard from './Dashboard';
import MonitorDetail from './MonitorDetail';
import Settings from './Settings';
import './App.css';

const PlaceholderView = ({ title, icon, message }) => (
  <div className="placeholder-view">
    <span className="icon" style={{ fontSize: '4rem', marginBottom: '1rem' }}>{icon}</span>
    <h3>{title}</h3>
    <p>{message}</p>
  </div>
);

function App() {
  const { isAuthenticated, loading } = useAuth();
  const [globalStats, setGlobalStats] = useState({ total: 0, up: 0, down: 0 });

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loader-alt"></div>
        <span>Establishing secure connection...</span>
      </div>
    );
  }

  return (
    <Router>
      <Routes>
        <Route
          path="/login"
          element={!isAuthenticated ? <Login /> : <Navigate to="/" />}
        />

        {/* Protected Layout Routes */}
        <Route element={isAuthenticated ? <Layout stats={globalStats} /> : <Navigate to="/login" />}>
          <Route path="/" element={<Dashboard setGlobalStats={setGlobalStats} />} />
          <Route path="/monitor/:id" element={<MonitorDetail />} />
          <Route
            path="/incidents"
            element={<PlaceholderView title="Incidents Log" icon="🚨" message="Real-time incident tracking coming soon." />}
          />
          <Route
            path="/settings"
            element={<Settings />}
          />
        </Route>

        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;
