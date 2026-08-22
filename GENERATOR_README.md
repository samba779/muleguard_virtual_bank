# MuleGuard Synthetic Data Generator

## Overview
This Python script generates realistic synthetic banking data for the MuleGuard fraud detection project. It creates customers, accounts, and transactions with different behavioral patterns to test fraud detection algorithms.

## Features
- **Realistic Behavioral Patterns**: Normal users, active legitimate users, and synthetic mule-like scenarios
- **Configurable Scale**: Multiple pre-configured sizes from small to production
- **Database Integration**: Direct PostgreSQL integration with proper constraints
- **Temporal Data**: Transactions distributed over configurable time periods
- **Safety Features**: Prevents self-transfers and respects database constraints

## Installation

### Prerequisites
- Python 3.7+
- PostgreSQL 12+
- Required Python packages:
  ```bash
  pip install psycopg2-binary faker
  ```

### Database Setup
Ensure your PostgreSQL database is running and accessible. Copy `.env.example` to `.env` and update the connection parameters:

```bash
cp .env.example .env
```

Edit `.env` with your database credentials:
```
DB_HOST=localhost
DB_DATABASE=muleguard_bank
DB_USER=postgres
DB_PASSWORD=your_password_here
```

**Security Note**: Never commit `.env` to version control. It's included in `.gitignore`.

## Usage

### Command Line
```bash
# Small dataset (10 customers, 10 accounts, 50 transactions)
python synthetic_data_generator.py small

# Medium dataset (50 customers, 100 accounts, 1000 transactions)
python synthetic_data_generator.py medium

# Large dataset (200 customers, 500 accounts, 10000 transactions)
python synthetic_data_generator.py large

# Production dataset (1000 customers, 2500 accounts, 100000 transactions)
python synthetic_data_generator.py production
```

### Programmatic Usage
```python
from synthetic_data_generator import SyntheticDataGenerator, MEDIUM_CONFIG

generator = SyntheticDataGenerator(DB_PARAMS)
generator.connect()
generator.generate_customers(MEDIUM_CONFIG['num_customers'])
generator.generate_accounts(MEDIUM_CONFIG['num_accounts'], MEDIUM_CONFIG['behavior_distribution'])
generator.generate_transactions(MEDIUM_CONFIG['num_transactions'], None, MEDIUM_CONFIG['time_range_days'])
generator.close()
```

## Configuration Options

### Pre-configured Sizes

| Config | Customers | Accounts | Transactions | Time Range | Normal | Active | Mule-like |
|--------|-----------|----------|--------------|------------|--------|--------|-----------|
| Small  | 10        | 10       | 50           | 30 days    | 40%    | 30%    | 30%       |
| Medium | 50        | 100      | 1,000        | 60 days    | 50%    | 30%    | 20%       |
| Large  | 200       | 500      | 10,000       | 90 days    | 60%    | 25%    | 15%       |
| Production | 1,000  | 2,500    | 100,000      | 180 days   | 70%    | 20%    | 10%       |

### Custom Configuration
Edit `generator_config.py` to add custom configurations:

```python
CUSTOM_CONFIG = {
    'num_customers': 100,
    'num_accounts': 200,
    'num_transactions': 5000,
    'time_range_days': 45,
    'behavior_distribution': {
        'types': ['normal', 'active_user', 'synthetic_mule_like'],
        'weights': [0.5, 0.3, 0.2]
    }
}
```

## Behavioral Patterns

### Normal Users
- Occasional transactions (1-3 per week)
- Random counterparties
- Transaction amounts: ₹500 - ₹15,000
- Channels: UPI, NEFT

### Active Legitimate Users
- Frequent transactions (daily)
- Regular counterparties (business relationships)
- Transaction amounts: ₹5,000 - ₹50,000
- Channels: UPI, IMPS, NEFT
- Higher account balances

### Synthetic Mule-like Scenarios
1. **Rapid Flow**: Quick incoming followed by outgoing transfers
2. **Many Counterparties**: Multiple different counterparties in short periods
3. **Concentration**: Multiple accounts transferring to single destination
4. **Random**: Mixed suspicious patterns
- Transaction amounts: ₹1,000 - ₹15,000
- Channels: UPI, IMPS
- Lower account balances

## Database Schema Compatibility

The generator is designed to work with the MuleGuard database schema:
- `customers` table with synthetic customer data
- `accounts` table with behavior labels (`account_label`)
- `transactions` table with directional sender/receiver relationships
- Respects all CHECK constraints (no self-transfers, valid enum values)

## Output Statistics

The generator provides the following statistics:
- Total customers, accounts, transactions
- Account distribution by behavior type
- Transaction distribution by type and status
- Balance statistics by behavior type
- Transaction counts and unique counterparty analysis

## Error Handling

The generator includes comprehensive error handling:
- Database connection failures
- Constraint violations
- Transaction rollbacks on errors
- Clear error messages

## Security Notes

- Never commit database credentials to version control
- Use environment variables for sensitive data in production
- The generator uses synthetic data only - no real financial information
- Database credentials are stored in `.env` file (not committed to git)
- `.env.example` is provided as a template for required environment variables

## Troubleshooting

### Connection Issues
```
✗ Connection failed: connection refused
```
- Verify PostgreSQL is running
- Check host, port, and credentials
- Ensure database exists

### Constraint Violations
```
✗ new row violates check constraint
```
- Ensure schema matches expected structure
- Check that behavior types match enum values
- Verify account types are valid

### Self-Transfer Prevention
The generator includes multiple safety checks to prevent self-transfers:
- Logic checks in parameter generation
- Final validation before insertion
- Database-level CHECK constraint

## Future Enhancements

Potential improvements for the generator:
- Geographic location data
- Device information
- Transaction categories/merchant codes
- Seasonal patterns
- Custom scenario templates
- Data export options (CSV, JSON)

## License

This is part of the MuleGuard student project for educational purposes.