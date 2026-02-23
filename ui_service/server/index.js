const express = require('express');
const redis = require('redis');
const axios = require('axios');
const cors = require('cors');
const path = require('path');

const app = express();
const port = process.env.PORT || 3000;

// --- Configuration ---
const REDIS_HOST = process.env.REDIS_HOST || 'redis';
const REDIS_PORT = process.env.REDIS_PORT || '6379';
const REDIS_URL = process.env.REDIS_URL || `redis://${REDIS_HOST}:${REDIS_PORT}`;
const USER_SERVICE_URL = process.env.USER_SERVICE_URL || 'http://user_service:5000';

app.use(cors());
app.use(express.json());

// Redis setup
const client = redis.createClient({ url: REDIS_URL });
client.on('error', (err) => console.log('Redis Client Error', err));
client.connect();

app.get('/health', (req, res) => {
    res.json({ status: 'healthy', service: 'ui_gateway' });
});

/**
 * Forward requests to the User Service and propagate auth headers.
 */
const userProxy = async (req, res, method, urlPath, data = null) => {
    try {
        const headers = {};
        if (req.headers.authorization) {
            headers.authorization = req.headers.authorization;
        }

        const config = {
            method: method,
            url: `${USER_SERVICE_URL}${urlPath}`,
            headers: headers,
            data: data
        };

        const response = await axios(config);
        res.status(response.status).json(response.data);
    } catch (error) {
        const status = error.response ? error.response.status : 500;
        const msg = error.response ? error.response.data : { error: 'Service Unavailable' };
        console.error(`Proxy Error [${method} ${urlPath}]:`, error.message);
        res.status(status).json(msg);
    }
};

// Auth and Profile Proxy Routes
app.post('/api/register', (req, res) => userProxy(req, res, 'POST', '/register', req.body));
app.post('/api/login', (req, res) => userProxy(req, res, 'POST', '/login', req.body));
app.get('/api/monitors/:id/incidents', (req, res) => userProxy(req, res, 'GET', `/monitors/${req.params.id}/incidents`));
app.get('/api/profile', (req, res) => userProxy(req, res, 'GET', '/profile'));
app.put('/api/profile', (req, res) => userProxy(req, res, 'PUT', '/profile', req.body));

// Monitor Management
app.get('/api/monitors', (req, res) => userProxy(req, res, 'GET', '/monitors'));
app.post('/api/monitors', (req, res) => userProxy(req, res, 'POST', '/monitors', req.body));
app.delete('/api/monitors/:id', async (req, res) => {
    const { id } = req.params;
    try {
        // Delete from Postgres via User Service
        const headers = req.headers.authorization ? { authorization: req.headers.authorization } : {};
        const response = await axios.delete(`${USER_SERVICE_URL}/monitors/${id}`, { headers });

        // Clear associated entries from Redis cache
        await Promise.all([
            client.del(`monitor:${id}:status`),
            client.del(`monitor:${id}:history`),
            client.del(`monitor:${id}:last_logged_state`)
        ]);

        res.json(response.data);
    } catch (error) {
        const status = error.response ? error.response.status : 500;
        const msg = error.response ? error.response.data : { error: 'Failed to delete monitor' };
        res.status(status).json(msg);
    }
});

// Direct Redis Access for Real-time Stats
app.get('/api/status/:id', async (req, res) => {
    try {
        const status = await client.get(`monitor:${req.params.id}:status`);
        res.json(status ? JSON.parse(status) : null);
    } catch (error) {
        console.error('Error fetching status from Redis:', error.message);
        res.status(500).json({ error: 'Failed to fetch status' });
    }
});

app.get('/api/history/:id', async (req, res) => {
    try {
        const history = await client.lRange(`monitor:${req.params.id}:history`, 0, 19);
        res.json(history.map(item => JSON.parse(item)).reverse());
    } catch (error) {
        console.error('Error fetching history from Redis:', error.message);
        res.status(500).json({ error: 'Failed to fetch history' });
    }
});

// Serve static frontend assets
app.use(express.static(path.join(__dirname, '../client/dist')));

// Fallback to index.html for SPA routing
app.use((req, res) => {
    res.sendFile(path.join(__dirname, '../client/dist/index.html'));
});

app.listen(port, () => {
    console.log(`UI Gateway listening at http://localhost:${port}`);
});
