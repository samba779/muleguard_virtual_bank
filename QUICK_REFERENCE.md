# MuleGuard Database Quick Reference

## Essential Database Information

**Database**: `muleguard_bank`  
**Connection**: See `.env` file for credentials  
**Current Dataset**: 50 customers, 100 accounts, 1,000 transactions

---

## Schema Quick Reference

### Core Tables
- **customers**: customer_id, name, email, phone, created_at
- **accounts**: account_id, customer_id, account_number, account_type, account_label, balance, status, created_at
- **transactions**: transaction_id, sender_account_id, receiver_account_id, amount, timestamp, transaction_type, status, channel, reference

### Important Fields
- `account_label` → Ground truth: 'normal', 'active_user', 'synthetic_mule_like'
- `sender_account_id` / `receiver_account_id` → Transaction direction (for graph analysis)
- `timestamp` → Temporal analysis support

---

## Essential Queries

### Get All Accounts with Labels
```sql
SELECT account_id, account_number, account_label, balance, status 
FROM accounts 
ORDER BY account_label, account_id;
```

### Get Transactions for an Account
```sql
SELECT t.transaction_id, 
       s.account_number as sender, 
       r.account_number as receiver, 
       t.amount, 
       t.timestamp, 
       t.transaction_type,
       t.status
FROM transactions t
JOIN accounts s ON t.sender_account_id = s.account_id
JOIN accounts r ON t.receiver_account_id = r.account_id
WHERE s.account_id = :account_id OR r.account_id = :account_id
ORDER BY t.timestamp DESC;
```

### Transaction Velocity (per account per day)
```sql
SELECT a.account_number, a.account_label,
       DATE(t.timestamp) as transaction_date,
       COUNT(*) as transactions_per_day
FROM transactions t
JOIN accounts a ON t.sender_account_id = a.account_id
GROUP BY a.account_number, a.account_label, DATE(t.timestamp)
ORDER BY transactions_per_day DESC;
```

### Incoming/Outgoing Summary
```sql
SELECT a.account_number, a.account_label,
       COUNT(CASE WHEN t.sender_account_id = a.account_id THEN 1 END) as outgoing_count,
       COUNT(CASE WHEN t.receiver_account_id = a.account_id THEN 1 END) as incoming_count,
       SUM(CASE WHEN t.sender_account_id = a.account_id THEN t.amount ELSE 0 END) as outgoing_amount,
       SUM(CASE WHEN t.receiver_account_id = a.account_id THEN t.amount ELSE 0 END) as incoming_amount
FROM accounts a
LEFT JOIN transactions t ON t.sender_account_id = a.account_id OR t.receiver_account_id = a.account_id
GROUP BY a.account_number, a.account_label;
```

### Unique Counterparties
```sql
SELECT a.account_number, a.account_label,
       COUNT(DISTINCT CASE WHEN t.sender_account_id = a.account_id THEN t.receiver_account_id END) as unique_receivers,
       COUNT(DISTINCT CASE WHEN t.receiver_account_id = a.account_id THEN t.sender_account_id END) as unique_senders
FROM accounts a
LEFT JOIN transactions t ON t.sender_account_id = a.account_id OR t.receiver_account_id = a.account_id
GROUP BY a.account_number, a.account_label
ORDER BY (unique_receivers + unique_senders) DESC;
```

### Graph Edge Data (for network analysis)
```sql
SELECT 
    s.account_id as source_node,
    r.account_id as target_node,
    s.account_label as source_label,
    r.account_label as target_label,
    COUNT(*) as edge_weight,
    SUM(t.amount) as total_amount
FROM transactions t
JOIN accounts s ON t.sender_account_id = s.account_id
JOIN accounts r ON t.receiver_account_id = r.account_id
GROUP BY s.account_id, r.account_id, s.account_label, r.account_label;
```

---

## Behavioral Patterns Reference

### Normal Users
- Transaction count: ~20 per account
- Balance: ~₹62K average
- Channels: UPI, NEFT
- Pattern: Stable, occasional transactions

### Active Users  
- Transaction count: ~20 per account
- Balance: ~₹286K average
- Channels: UPI, IMPS, NEFT
- Pattern: High frequency, legitimate business

### Mule-like Scenarios
- Transaction count: ~18 per account
- Balance: ~₹30K average
- Channels: UPI, IMPS
- Pattern: Rapid flow, many counterparties, concentration

---

## Data Generator Commands

```bash
# Small test dataset
python synthetic_data_generator.py small

# Medium dataset (current)
python synthetic_data_generator.py medium

# Large dataset
python synthetic_data_generator.py large

# Production dataset
python synthetic_data_generator.py production
```

---

## Important Notes

1. **Ground Truth**: Use `account_label` for ML training - these are synthetic scenarios, not real fraud
2. **No Self-Transfers**: Database constraint prevents sender = receiver
3. **Transaction Direction**: Always preserved for graph analysis
4. **Synthetic Data**: All data is fake - no real financial information
5. **Security**: Credentials in `.env` file (not in git)

---

## Contact

**Database Owner**: Samba  
**Next Developer**: Bhanu (API/ML/Graph Analysis)  
**Project**: MuleGuard Fraud Detection Prototype