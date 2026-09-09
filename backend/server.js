const path = require('path');
require('dotenv').config({ path: [path.resolve(__dirname, '.env'), path.resolve(__dirname, '../.env')] });
const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');

const app = express();
app.use(cors());
app.use(express.json());

// Serve frontend static files and assets
app.use('/frontend', express.static(path.resolve(__dirname, '../frontend')));
app.use('/assets', express.static(path.resolve(__dirname, '../assets')));

// Redirect root to login page
app.get('/', (req, res) => {
    res.redirect('/frontend/login.html');
});

const pool = new Pool({
    user: process.env.DB_USER,
    host: process.env.DB_HOST,
    database: process.env.DB_DATABASE,
    password: process.env.DB_PASSWORD,
    port: process.env.DB_PORT || 5432,
});

// ─── Deterministic enrichment helpers ────────────────────────────────────────
// These generate stable per-account synthetic metadata (phone, device, IP, address)
// from the account_id so values are consistent across reloads, since the DB schema
// doesn't store these fields but the UI rule engine uses them.

function hashCode(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = ((hash << 5) - hash) + str.charCodeAt(i);
        hash |= 0;
    }
    return Math.abs(hash);
}

const DEVICES = ['IPHONE_15_PRO', 'SAMSUNG_S24', 'MACBOOK_PRO_M3', 'IPAD_AIR', 'DELL_LATITUDE', 'THINKPAD_T14', 'MACBOOK_AIR', 'IPHONE_14', 'PIXEL_8'];
const CITIES = ['Mumbai', 'Delhi', 'Chennai', 'Bangalore', 'Kolkata', 'Hyderabad', 'Pune', 'Ahmedabad', 'Jaipur', 'Kochi'];
const AREAS = ['Sector 14', 'MG Road', 'Anna Nagar', 'Koramangala', 'Salt Lake', 'Banjara Hills', 'Viman Nagar', 'CG Road', 'Malviya Nagar', 'Marine Drive'];

function enrichAccount(row) {
    const h = hashCode(row.account_number);
    const phone = `+91 ${(70000 + (h % 30000)).toString()} ${(10000 + ((h >> 8) % 90000)).toString().padStart(5, '0')}`;
    const device = DEVICES[h % DEVICES.length];
    const ip = `${10 + (h % 190)}.${(h >> 4) % 256}.${(h >> 8) % 256}.${(h >> 12) % 256}`;
    const city = CITIES[h % CITIES.length];
    const area = AREAS[(h >> 3) % AREAS.length];
    const address = `Flat ${100 + (h % 900)}, ${area}, ${city}`;

    // Map DB labels to UI status
    let uiStatus = 'Normal';
    if (row.account_label === 'synthetic_mule_like') uiStatus = 'Flagged';
    else if (row.status === 'frozen') uiStatus = 'Blocked';
    else if (row.status === 'closed') uiStatus = 'Blocked';

    // Map DB account_type
    const uiType = row.account_type === 'current' ? 'Current' : 'Savings';

    // Baseline risk score from label
    let baseRisk = 15;
    if (row.account_label === 'synthetic_mule_like') baseRisk = 65;
    else if (row.account_label === 'active_user') baseRisk = 25;

    const created = row.created_at ? new Date(row.created_at).toISOString().split('T')[0] : '2025-01-01';

    return {
        id: row.account_number,
        name: row.name,
        type: uiType,
        balance: parseFloat(row.balance),
        riskScore: baseRisk,
        status: uiStatus,
        created: created,
        phone: phone,
        device: device,
        ip: ip,
        address: address,
        scenario: row.account_label === 'synthetic_mule_like' ? 'Mule-Like Behavior' :
                  row.account_label === 'active_user' ? 'Active Legitimate' : 'Normal Legitimate'
    };
}

function formatRelativeTime(timestamp) {
    if (!timestamp) return 'Unknown';
    const now = Date.now();
    const txTime = new Date(timestamp).getTime();
    const diffMs = now - txTime;
    const diffMin = Math.floor(diffMs / 60000);

    if (diffMin < 1) return 'Just now';
    if (diffMin < 60) return `${diffMin} min ago`;
    const diffHrs = Math.floor(diffMin / 60);
    if (diffHrs < 24) return `${diffHrs} hr${diffHrs > 1 ? 's' : ''} ago`;
    const diffDays = Math.floor(diffHrs / 24);
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
}

function formatINR(amount) {
    return '₹' + Math.round(amount).toLocaleString('en-IN');
}

function enrichTransaction(row, index) {
    const amount = parseFloat(row.amount);
    const isoTimestamp = row.timestamp ? new Date(row.timestamp).toISOString() : new Date().toISOString();
    const txType = row.transaction_type ? row.transaction_type.charAt(0).toUpperCase() + row.transaction_type.slice(1) : 'Transfer';

    // Map DB status to UI status
    let uiStatus = 'Normal';
    if (row.status === 'pending') uiStatus = 'Under Review';
    else if (row.status === 'failed') uiStatus = 'Flagged';
    else if (row.status === 'cancelled') uiStatus = 'Blocked';

    return {
        id: `TX-${String(row.transaction_id).padStart(4, '0')}`,
        senderId: row.sender_number,
        receiverId: row.receiver_number,
        amountNumeric: amount,
        type: txType,
        value: formatINR(amount),
        score: 20, // Baseline — rule engine will recalculate
        time: formatRelativeTime(row.timestamp),
        isoTimestamp: isoTimestamp,
        timestamp: isoTimestamp,
        origin: 'India',
        destination: 'India',
        status: uiStatus,
        channel: row.channel ? row.channel.toUpperCase() : 'UPI',
        summary: `${txType} via ${(row.channel || 'upi').toUpperCase()}`
    };
}

// ─── API Endpoints ───────────────────────────────────────────────────────────

// Get all accounts (with customer name joined in)
app.get('/api/accounts', async (req, res) => {
    try {
        const result = await pool.query(`
      SELECT a.account_id, a.account_number, c.name, a.account_label, a.balance, a.status
      FROM accounts a
      JOIN customers c ON a.customer_id = c.customer_id
    `);
        res.json(result.rows);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Failed to fetch accounts' });
    }
});

// Get recent transactions
app.get('/api/transactions', async (req, res) => {
    try {
        const result = await pool.query(
            'SELECT * FROM transactions ORDER BY timestamp DESC LIMIT 100'
        );
        res.json(result.rows);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Failed to fetch transactions' });
    }
});

// Combined endpoint — returns the FULL data shape for the frontend UI
app.get('/api/muleguard-data', async (req, res) => {
    try {
        // 1. Fetch accounts with customer info
        const accountsResult = await pool.query(`
            SELECT a.account_number, c.name, a.account_type, a.account_label,
                   a.balance, a.status, a.created_at
            FROM accounts a
            JOIN customers c ON a.customer_id = c.customer_id
            ORDER BY a.account_number
        `);

        // 2. Fetch all transactions with sender/receiver account numbers
        const txResult = await pool.query(`
            SELECT t.transaction_id, sa.account_number AS sender_number,
                   ra.account_number AS receiver_number, t.amount,
                   t.transaction_type, t.status, t.channel, t.timestamp
            FROM transactions t
            JOIN accounts sa ON t.sender_account_id = sa.account_id
            JOIN accounts ra ON t.receiver_account_id = ra.account_id
            ORDER BY t.timestamp DESC
        `);

        // 3. Build keyed accounts object (UI expects { "ACC0001": {...}, "ACC0002": {...} })
        const accounts = {};
        accountsResult.rows.forEach(row => {
            const enriched = enrichAccount(row);
            accounts[enriched.id] = enriched;
        });

        // 4. Build transactions array
        const transactions = txResult.rows.map((row, i) => enrichTransaction(row, i));

        // 5. Return the full UI-compatible data shape
        // Rules, alerts, cases, networks, decisions, auditLogs are initialized empty
        // so the client-side rule engine + ML model populates them on first load
        const payload = {
            rules: [
                { id: 'R-VEL-1', name: 'Velocity Spike (Inbound Degree)', threshold: 5, unit: 'transfers/24h', description: 'Triggers when an account receives more than the threshold of inbound UPI transfers in a 24-hour period.', active: true },
                { id: 'R-HOLD-1', name: 'Short Holding Time Ratio', threshold: 80, unit: '% ratio', description: 'Triggers when more than the threshold of received funds are transferred out of the account within 30 minutes.', active: true },
                { id: 'R-NET-1', name: 'Suspicious Component Connection', threshold: 1, unit: 'hops', description: 'Triggers when a node has direct connection (shared device/IP/phone) to previously blocked/flagged fraud nodes.', active: true },
                { id: 'R-VAL-1', name: 'High-Value Shell Transfer', threshold: 100000, unit: 'INR', description: 'Triggers on a transfer exceeding threshold from/to newly registered corporate shell entities.', active: true },
                { id: 'R-CIRC-1', name: 'Circular Money Flow', threshold: 1, unit: 'cycles', description: 'Triggers when an account participates in a closed money flow loop of connected accounts.', active: true },
                { id: 'R-DORM-1', name: 'Dormant Account Activation', threshold: 50000, unit: 'INR/24h', description: 'Triggers when a previously inactive/dormant account receives significant transaction volume within 24 hours.', active: true }
            ],
            accounts: accounts,
            transactions: transactions,
            alerts: [],
            cases: [],
            decisions: [],
            auditLogs: [
                { id: 'LOG-0001', actor: 'System Engine', action: 'Connected to PostgreSQL database', time: 'Just now', details: `Loaded ${Object.keys(accounts).length} accounts and ${transactions.length} transactions from muleguard_bank.` }
            ],
            networks: {
                'NET-0001': {
                    id: 'NET-0001',
                    name: 'Gokhale High-Velocity Fan-Out',
                    type: 'Mule Aggregator Ring',
                    score: 94,
                    members: 5,
                    totalValue: '₹4,85,000',
                    connectedCount: 58,
                    lastActivity: 'Just now',
                    status: 'Flagged',
                    summary: 'High-frequency transaction hub centered on Udyati Gokhale (ACC0003) routing multiple incoming UPI transfers to sub-mule nodes.',
                    graphNodes: [
                        { id: 'ACC0003', label: 'U. Gokhale (Hub)', role: 'Primary Mule Hub', risk: 'Critical', cx: 200, cy: 80, r: 16 },
                        { id: 'ACC0063', label: 'D. Atwal', role: 'Sub-Clearing Node', risk: 'High', cx: 80, cy: 40, r: 12 },
                        { id: 'ACC0097', label: 'C. Doshi', role: 'Layering Conduit', risk: 'High', cx: 80, cy: 120, r: 12 },
                        { id: 'ACC0080', label: 'K. Raj', role: 'Terminal Cashout', risk: 'High', cx: 320, cy: 40, r: 12 },
                        { id: 'ACC0009', label: 'H. Parekh', role: 'Intermediary Smurfer', risk: 'High', cx: 320, cy: 120, r: 12 }
                    ],
                    graphLinks: [
                        { source: 0, target: 1, flow: true },
                        { source: 0, target: 2, flow: true },
                        { source: 0, target: 3, flow: true },
                        { source: 0, target: 4, flow: true },
                        { source: 2, target: 0, flow: true }
                    ]
                },
                'NET-0002': {
                    id: 'NET-0002',
                    name: 'Rattan Multi-Account Ring',
                    type: 'Synthetic Identity Link',
                    score: 88,
                    members: 4,
                    totalValue: '₹3,20,000',
                    connectedCount: 14,
                    lastActivity: '12 min ago',
                    status: 'Flagged',
                    summary: 'Multiple savings/current accounts registered under identical persona Hredhaan Rattan exhibiting coordinated fund movements.',
                    graphNodes: [
                        { id: 'ACC0015', label: 'H. Rattan (Cur 1)', role: 'Corporate Front', risk: 'Critical', cx: 120, cy: 60, r: 14 },
                        { id: 'ACC0020', label: 'H. Rattan (Sav 1)', role: 'Personal Reserve', risk: 'High', cx: 280, cy: 60, r: 14 },
                        { id: 'ACC0056', label: 'H. Rattan (Cur 2)', role: 'Layering Node', risk: 'High', cx: 200, cy: 130, r: 14 },
                        { id: 'ACC0023', label: 'F. Mistry', role: 'External Feeder', risk: 'Medium', cx: 200, cy: 20, r: 12 }
                    ],
                    graphLinks: [
                        { source: 3, target: 0, flow: true },
                        { source: 0, target: 1, flow: true },
                        { source: 1, target: 2, flow: true },
                        { source: 2, target: 0, flow: true }
                    ]
                },
                'NET-0003': {
                    id: 'NET-0003',
                    name: 'Doshi Cross-Layering Syndicate',
                    type: 'Layering Loop',
                    score: 82,
                    members: 3,
                    totalValue: '₹2,65,000',
                    connectedCount: 9,
                    lastActivity: '45 min ago',
                    status: 'Under Review',
                    summary: 'Cross-account structuring between Chameli Doshi accounts (ACC0065 & ACC0097) utilizing intermediary transfers to obscure origin of funds.',
                    graphNodes: [
                        { id: 'ACC0065', label: 'C. Doshi (Sav)', role: 'Inbound Ingestion', risk: 'High', cx: 100, cy: 80, r: 14 },
                        { id: 'ACC0097', label: 'C. Doshi (Cur)', role: 'Outbound Layerer', risk: 'High', cx: 300, cy: 80, r: 14 },
                        { id: 'ACC0010', label: 'H. Parikh', role: 'Intermediary Bridge', risk: 'Medium', cx: 200, cy: 120, r: 12 }
                    ],
                    graphLinks: [
                        { source: 0, target: 2, flow: true },
                        { source: 2, target: 1, flow: true },
                        { source: 1, target: 0, flow: true }
                    ]
                }
            }
        };

        res.json(payload);
    } catch (err) {
        console.error('Failed to build muleguard-data payload:', err);
        res.status(500).json({ error: 'Failed to fetch muleguard data' });
    }
});

app.listen(5000, () => console.log('MuleGuard API running on http://localhost:5000'));