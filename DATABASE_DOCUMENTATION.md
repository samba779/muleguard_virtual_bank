# MuleGuard Virtual Bank Database Documentation

## Overview
This documentation describes the MuleGuard Virtual Bank PostgreSQL database and synthetic dataset, designed for fraud detection testing and behavioral analysis.

**Database Name**: `muleguard_bank`  
**PostgreSQL Version**: 17.11  
**Purpose**: Synthetic banking data for MuleGuard fraud detection prototype  

---

## Database Schema

### Table: `customers`
Stores synthetic bank customer information.

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| customer_id | BIGINT | PRIMARY KEY, GENERATED ALWAYS AS IDENTITY | Unique customer identifier |
| name | VARCHAR(100) | NOT NULL | Customer's full name |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Customer email address |
| phone | VARCHAR(20) | UNIQUE | Customer phone number |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Account creation timestamp |

**Indexes**: 
- Primary key on `customer_id`
- Unique constraints on `email` and `phone`

**Relationships**: 
- One-to-many with `accounts` table

---

### Table: `accounts`
Stores bank accounts linked to customers with behavior labels for testing.

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| account_id | BIGINT | PRIMARY KEY, GENERATED ALWAYS AS IDENTITY | Unique account identifier |
| customer_id | BIGINT | NOT NULL, FOREIGN KEY → customers(customer_id) | Link to customer |
| account_number | VARCHAR(20) | UNIQUE, NOT NULL | Human-readable account number |
| account_type | VARCHAR(20) | NOT NULL, CHECK (account_type IN ('savings', 'current')) | Type of bank account |
| account_label | VARCHAR(50) | NOT NULL, CHECK (account_label IN ('normal', 'active_user', 'synthetic_mule_like')) | Behavior scenario label |
| balance | DECIMAL(15,2) | NOT NULL, DEFAULT 0.00, CHECK (balance >= 0) | Current account balance |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'active', CHECK (status IN ('active', 'closed', 'frozen')) | Account status |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Account creation timestamp |

**Indexes**:
- `idx_accounts_customer` ON customer_id
- `idx_accounts_status` ON status  
- `idx_accounts_label` ON account_label

**Relationships**: 
- Many-to-one with `customers` table
- One-to-many with `transactions` table (as sender or receiver)

**Important Notes**:
- `account_label` is the ground truth for behavioral analysis
- Each account can have different behavior even if owned by same customer
- Supports future ML model training and validation

---

### Table: `transactions`
Stores all money transfers between accounts with directional information.

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| transaction_id | BIGINT | PRIMARY KEY, GENERATED ALWAYS AS IDENTITY | Unique transaction identifier |
| sender_account_id | BIGINT | NOT NULL, FOREIGN KEY → accounts(account_id) | Account sending money |
| receiver_account_id | BIGINT | NOT NULL, FOREIGN KEY → accounts(account_id) | Account receiving money |
| amount | DECIMAL(15,2) | NOT NULL, CHECK (amount > 0) | Transaction amount |
| timestamp | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | When transaction occurred |
| transaction_type | VARCHAR(20) | NOT NULL, CHECK (transaction_type IN ('transfer', 'payment', 'deposit', 'withdrawal')) | Type of transaction |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'completed', CHECK (status IN ('completed', 'pending', 'failed', 'cancelled')) | Transaction status |
| channel | VARCHAR(20) | CHECK (channel IN ('upi', 'neft', 'rtgs', 'imps', 'atm', 'branch')) | Transaction channel (optional) |
| reference | VARCHAR(100) | | Transaction reference/notes (optional) |

**Indexes**:
- `idx_transactions_sender` ON sender_account_id
- `idx_transactions_receiver` ON receiver_account_id
- `idx_transactions_timestamp` ON timestamp
- `idx_transactions_type` ON transaction_type
- `idx_transactions_status` ON status

**Constraints**:
- `CHECK (sender_account_id != receiver_account_id)` - Prevents self-transfers

**Relationships**: 
- Many-to-one with `accounts` table (both sender and receiver)

**Important Notes**:
- Transaction direction is preserved (sender → receiver)
- Essential for graph analysis (accounts = nodes, transactions = directed edges)
- Supports behavioral analysis and money flow tracing

---

## Entity Relationship Diagram

```
customers (1) ──────< (N) accounts (1) ──────< (N) transactions
                                                ↑
                                                │
                                                (N)
```

**Relationships**:
- One customer can have multiple accounts
- One account can be involved in multiple transactions (as sender or receiver)
- One transaction connects exactly two accounts (sender and receiver)

---

## Current Dataset Details

### Medium Configuration (Current Dataset)
- **Customers**: 50
- **Accounts**: 100
- **Transactions**: 1,000
- **Time Range**: 60 days
- **Generated**: August 22, 2026

### Account Distribution by Behavior Type
| Behavior Type | Count | Percentage | Avg Balance | Avg Transactions/Account |
|---------------|-------|------------|-------------|-------------------------|
| normal | 41 | 41% | ₹62,454 | 20.7 |
| active_user | 39 | 39% | ₹286,251 | 20.3 |
| synthetic_mule_like | 20 | 20% | ₹29,576 | 17.9 |

### Transaction Distribution
| Transaction Type | Count | Percentage |
|------------------|-------|------------|
| transfer | 493 | 49.3% |
| payment | 507 | 50.7% |

| Transaction Status | Count | Percentage |
|-------------------|-------|------------|
| completed | 955 | 95.5% |
| pending | 21 | 2.1% |
| failed | 14 | 1.4% |
| cancelled | 10 | 1.0% |

---

## Behavioral Patterns

### Normal Users
**Characteristics**:
- Occasional transactions (1-3 per week)
- Stable counterparties over time
- Transaction amounts: ₹500 - ₹15,000
- Channels: UPI, NEFT
- Balanced incoming/outgoing ratios

**Purpose**: Represents everyday banking behavior to establish baseline patterns.

### Active Legitimate Users
**Characteristics**:
- High transaction frequency (daily)
- Regular counterparties (business relationships)
- Transaction amounts: ₹5,000 - ₹50,000
- Channels: UPI, IMPS, NEFT
- Higher account balances (₹50K - ₹500K)
- Legitimate business patterns

**Purpose**: Critical for preventing false positives - shows that high activity ≠ fraud.

### Synthetic Mule-like Scenarios
**Characteristics**:
- Rapid incoming → outgoing transfers
- Many counterparties in short periods
- Transaction concentration patterns
- Transaction amounts: ₹1,000 - ₹15,000
- Channels: UPI, IMPS
- Lower account balances

**Pattern Types**:
1. **Rapid Flow**: Quick incoming followed by outgoing transfers
2. **Many Counterparties**: Multiple different counterparties in short periods
3. **Concentration**: Multiple accounts transferring to single destination
4. **Random**: Mixed suspicious patterns

**Purpose**: Test scenarios for fraud detection algorithms, NOT confirmed fraud.

---

## Sample Queries for MuleGuard Analysis

### 1. Transaction Velocity (Transactions per Day)
```sql
SELECT 
    a.account_number, 
    a.account_label,
    DATE(t.timestamp) as transaction_date,
    COUNT(*) as transactions_per_day
FROM transactions t
JOIN accounts a ON t.sender_account_id = a.account_id
GROUP BY a.account_number, a.account_label, DATE(t.timestamp)
ORDER BY transactions_per_day DESC;
```

### 2. Incoming/Outgoing Analysis
```sql
SELECT 
    a.account_number, 
    a.account_label,
    COUNT(CASE WHEN t.sender_account_id = a.account_id THEN 1 END) as outgoing_count,
    COUNT(CASE WHEN t.receiver_account_id = a.account_id THEN 1 END) as incoming_count,
    SUM(CASE WHEN t.sender_account_id = a.account_id THEN t.amount ELSE 0 END) as outgoing_amount,
    SUM(CASE WHEN t.receiver_account_id = a.account_id THEN t.amount ELSE 0 END) as incoming_amount
FROM accounts a
LEFT JOIN transactions t ON t.sender_account_id = a.account_id OR t.receiver_account_id = a.account_id
GROUP BY a.account_number, a.account_label
ORDER BY a.account_label, outgoing_count DESC;
```

### 3. Unique Counterparties Analysis
```sql
SELECT 
    a.account_number, 
    a.account_label,
    COUNT(DISTINCT CASE WHEN t.sender_account_id = a.account_id THEN t.receiver_account_id END) as unique_receivers,
    COUNT(DISTINCT CASE WHEN t.receiver_account_id = a.account_id THEN t.sender_account_id END) as unique_senders,
    COUNT(DISTINCT CASE WHEN t.sender_account_id = a.account_id THEN t.receiver_account_id 
                       WHEN t.receiver_account_id = a.account_id THEN t.sender_account_id END) as total_unique_counterparties
FROM accounts a
LEFT JOIN transactions t ON t.sender_account_id = a.account_id OR t.receiver_account_id = a.account_id
GROUP BY a.account_number, a.account_label
ORDER BY total_unique_counterparties DESC;
```

### 4. Rapid Transfer Detection (Time Between Transactions)
```sql
WITH transaction_times AS (
    SELECT 
        account_id,
        timestamp,
        LAG(timestamp) OVER (PARTITION BY account_id ORDER BY timestamp) as prev_timestamp
    FROM (
        SELECT sender_account_id as account_id, timestamp FROM transactions
        UNION ALL
        SELECT receiver_account_id as account_id, timestamp FROM transactions
    ) all_transactions
)
SELECT 
    a.account_number,
    a.account_label,
    tt.timestamp,
    tt.prev_timestamp,
    EXTRACT(EPOCH FROM (tt.timestamp - tt.prev_timestamp))/60 as minutes_between_transactions
FROM transaction_times tt
JOIN accounts a ON tt.account_id = a.account_id
WHERE tt.prev_timestamp IS NOT NULL
  AND EXTRACT(EPOCH FROM (tt.timestamp - tt.prev_timestamp))/60 < 30  -- Less than 30 minutes
ORDER BY minutes_between_transactions ASC;
```

### 5. Graph Analysis Preparation (Account-to-Account Relationships)
```sql
SELECT 
    s.account_number as sender_account,
    s.account_label as sender_label,
    r.account_number as receiver_account,
    r.account_label as receiver_label,
    COUNT(*) as transaction_count,
    SUM(t.amount) as total_amount,
    MIN(t.timestamp) as first_transaction,
    MAX(t.timestamp) as last_transaction
FROM transactions t
JOIN accounts s ON t.sender_account_id = s.account_id
JOIN accounts r ON t.receiver_account_id = r.account_id
GROUP BY s.account_number, s.account_label, r.account_number, r.account_label
ORDER BY transaction_count DESC;
```

### 6. Temporal Behavior Changes (Compare Time Windows)
```sql
WITH time_windows AS (
    SELECT 
        a.account_number,
        a.account_label,
        COUNT(CASE WHEN t.timestamp >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as recent_tx_count,
        COUNT(CASE WHEN t.timestamp >= CURRENT_DATE - INTERVAL '30 days' AND t.timestamp < CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as previous_tx_count,
        COUNT(CASE WHEN t.timestamp >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END)::FLOAT / 
        NULLIF(COUNT(CASE WHEN t.timestamp >= CURRENT_DATE - INTERVAL '30 days' AND t.timestamp < CURRENT_DATE - INTERVAL '7 days' THEN 1 END), 0) as activity_ratio
    FROM accounts a
    LEFT JOIN transactions t ON t.sender_account_id = a.account_id OR t.receiver_account_id = a.account_id
    GROUP BY a.account_number, a.account_label
)
SELECT 
    account_number,
    account_label,
    recent_tx_count,
    previous_tx_count,
    activity_ratio,
    CASE 
        WHEN activity_ratio > 2.0 THEN 'Significant Increase'
        WHEN activity_ratio > 1.5 THEN 'Moderate Increase'
        WHEN activity_ratio < 0.5 THEN 'Significant Decrease'
        ELSE 'Stable'
    END as behavior_change
FROM time_windows
WHERE previous_tx_count > 0
ORDER BY activity_ratio DESC NULLS LAST;
```

### 7. Average Transaction Amount by Account
```sql
SELECT 
    a.account_number,
    a.account_label,
    COUNT(*) as transaction_count,
    AVG(t.amount) as avg_transaction_amount,
    MIN(t.amount) as min_amount,
    MAX(t.amount) as max_amount,
    STDDEV(t.amount) as amount_stddev
FROM accounts a
LEFT JOIN transactions t ON t.sender_account_id = a.account_id OR t.receiver_account_id = a.account_id
GROUP BY a.account_number, a.account_label
HAVING COUNT(*) > 0
ORDER BY avg_transaction_amount DESC;
```

---

## Database Connection Information

### Environment Configuration
The database credentials are stored in `.env` file (not committed to git):

```bash
DB_HOST=localhost
DB_DATABASE=muleguard_bank
DB_USER=postgres
DB_PASSWORD=your_password_here
```

### Connection Example (Python)
```python
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    database=os.getenv('DB_DATABASE'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)
```

### Connection Example (Direct SQL)
```bash
psql -h localhost -U postgres -d muleguard_bank
```

---

## Data Generation

### Synthetic Data Generator
The synthetic data is generated using `synthetic_data_generator.py`:

**Usage**:
```bash
python synthetic_data_generator.py small    # 10 customers, 10 accounts, 50 transactions
python synthetic_data_generator.py medium   # 50 customers, 100 accounts, 1,000 transactions
python synthetic_data_generator.py large    # 200 customers, 500 accounts, 10,000 transactions
python synthetic_data_generator.py production  # 1,000 customers, 2,500 accounts, 100,000 transactions
```

**Key Features**:
- Realistic Indian names and contact information (Faker library)
- Behavioral pattern generation based on account labels
- Temporal distribution over configurable time periods
- Safety checks to prevent self-transfers
- Multiple transaction channels and statuses

### Current Dataset Status
- **Configuration**: Medium
- **Generation Date**: August 22, 2026
- **Quality**: Verified - no self-transfers, all constraints respected
- **Behavioral Differentiation**: Clear patterns visible between account types

---

## Important Notes for API/ML Developer

### Ground Truth Labels
- `account_label` in accounts table provides ground truth for ML model training
- Values: `normal`, `active_user`, `synthetic_mule_like`
- **Important**: `synthetic_mule_like` are test scenarios, NOT confirmed fraud

### Data Limitations
- Synthetic data only - no real financial information
- Behavioral patterns are simulated, not from real fraud cases
- Geographic location and device information not included
- Limited to basic transaction types (transfer, payment, deposit, withdrawal)

### Graph Analysis Support
- Transaction direction preserved (sender → receiver)
- Easy to reconstruct account relationships
- Supports network analysis and money flow tracing
- Nodes = accounts, Edges = transactions

### Temporal Analysis Support
- Timestamps included for all transactions
- Supports hour-level, day-level, week-level, month-level analysis
- Time range can be extended using data generator

### Future Extensions
Consider adding for enhanced analysis:
- Geographic location data
- Device information
- Merchant categories
- Transaction frequency patterns
- Seasonal variations
- Customer demographics

---

## Security and Privacy

### Data Security
- All data is synthetic - no real customer information
- Database credentials stored in `.env` (excluded from git)
- `.gitignore` prevents accidental credential commits
- No PII (Personally Identifiable Information) included

### Access Control
- Currently running on local PostgreSQL
- Recommend implementing proper user roles for production
- Consider database encryption for sensitive deployments

---

## Handover Checklist

For the API/ML Developer (Bhanu):

- [x] Database schema documented
- [x] Table relationships explained
- [x] Sample queries provided for analysis
- [x] Behavioral patterns documented
- [x] Ground truth labels explained
- [x] Data generation process documented
- [x] Security considerations noted
- [x] Connection information provided
- [x] Current dataset details included
- [x] Graph analysis support confirmed
- [x] Temporal analysis support confirmed

---

## Contact and Support

### Database Responsibilities
- **Samba**: Virtual Bank, PostgreSQL, synthetic dataset, transaction generation
- **Questions**: Database schema, data generation, synthetic data quality

### Next Developer Responsibilities
- **Bhanu**: API, behavioral analysis, ML/risk model, explainability, graph analysis
- **Questions**: API integration, ML model development, feature engineering

### Project Context
- **Project**: MuleGuard - Student-level banking fraud/mule-account detection prototype
- **Purpose**: Analyze account behavior over time and transaction networks
- **Approach**: Risk indicators and explanations for bank investigator review
- **Important**: Does NOT automatically declare accounts fraudulent or make final decisions

---

**Documentation Version**: 1.0  
**Last Updated**: August 22, 2026  
**Database Version**: PostgreSQL 17.11  
**Dataset**: Medium Configuration (1,000 transactions)