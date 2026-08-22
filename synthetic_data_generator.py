"""
MuleGuard Synthetic Banking Data Generator
Generates realistic synthetic banking data for fraud detection testing.
"""

import random
import psycopg2
from datetime import datetime, timedelta
from faker import Faker
import sys
import os
from dotenv import load_dotenv
from generator_config import SMALL_CONFIG, MEDIUM_CONFIG, LARGE_CONFIG, PRODUCTION_CONFIG

# Load environment variables from .env file
load_dotenv()

# Initialize Faker for Indian context
fake = Faker('en_IN')

# Database connection parameters from environment variables
DB_PARAMS = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_DATABASE', 'muleguard_bank'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}

# Behavior types
BEHAVIOR_TYPES = ['normal', 'active_user', 'synthetic_mule_like']
ACCOUNT_TYPES = ['savings', 'current']
TRANSACTION_TYPES = ['transfer', 'payment', 'deposit', 'withdrawal']
TRANSACTION_CHANNELS = ['upi', 'neft', 'rtgs', 'imps', 'atm', 'branch']
TRANSACTION_STATUSES = ['completed', 'pending', 'failed', 'cancelled']

class SyntheticDataGenerator:
    def __init__(self, db_params):
        self.db_params = db_params
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**self.db_params)
            self.cursor = self.conn.cursor()
            print("✓ Connected to database")
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            sys.exit(1)
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("✓ Database connection closed")
    
    def clear_existing_data(self):
        """Clear existing data from tables"""
        try:
            self.cursor.execute("DELETE FROM transactions")
            self.cursor.execute("DELETE FROM accounts")
            self.cursor.execute("DELETE FROM customers")
            self.conn.commit()
            print("✓ Cleared existing data")
        except Exception as e:
            print(f"✗ Failed to clear data: {e}")
            self.conn.rollback()
    
    def generate_customers(self, num_customers):
        """Generate synthetic customers"""
        customers = []
        for i in range(num_customers):
            customer = {
                'name': fake.name(),
                'email': fake.email(),
                'phone': fake.phone_number()[:20]  # Limit to 20 chars
            }
            customers.append(customer)
        
        # Insert customers
        for customer in customers:
            self.cursor.execute(
                "INSERT INTO customers (name, email, phone) VALUES (%s, %s, %s)",
                (customer['name'], customer['email'], customer['phone'])
            )
        
        self.conn.commit()
        print(f"✓ Generated {num_customers} customers")
        return customers
    
    def generate_accounts(self, num_accounts, behavior_distribution):
        """Generate synthetic accounts with behavior labels"""
        accounts = []
        
        # Get customer IDs
        self.cursor.execute("SELECT customer_id FROM customers")
        customer_ids = [row[0] for row in self.cursor.fetchall()]
        
        for i in range(num_accounts):
            # Select behavior type based on distribution
            behavior_type = random.choices(
                behavior_distribution['types'],
                weights=behavior_distribution['weights'],
                k=1
            )[0]
            
            account = {
                'customer_id': random.choice(customer_ids),
                'account_number': f'ACC{i+1:04d}',
                'account_type': random.choice(ACCOUNT_TYPES),
                'account_label': behavior_type,
                'balance': self._generate_initial_balance(behavior_type),
                'status': 'active'
            }
            accounts.append(account)
        
        # Insert accounts
        for account in accounts:
            self.cursor.execute(
                """INSERT INTO accounts (customer_id, account_number, account_type, account_label, balance, status)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (account['customer_id'], account['account_number'], account['account_type'],
                 account['account_label'], account['balance'], account['status'])
            )
        
        self.conn.commit()
        print(f"✓ Generated {num_accounts} accounts")
        return accounts
    
    def _generate_initial_balance(self, behavior_type):
        """Generate realistic initial balance based on behavior type"""
        if behavior_type == 'normal':
            return round(random.uniform(10000, 100000), 2)
        elif behavior_type == 'active_user':
            return round(random.uniform(50000, 500000), 2)
        else:  # synthetic_mule_like
            return round(random.uniform(5000, 50000), 2)
    
    def generate_transactions(self, num_transactions, accounts, time_range_days=30):
        """Generate synthetic transactions with realistic patterns"""
        transactions = []
        
        # Get account IDs by behavior type
        self.cursor.execute("SELECT account_id, account_label FROM accounts")
        account_info = {row[0]: row[1] for row in self.cursor.fetchall()}
        
        normal_accounts = [aid for aid, label in account_info.items() if label == 'normal']
        active_accounts = [aid for aid, label in account_info.items() if label == 'active_user']
        mule_accounts = [aid for aid, label in account_info.items() if label == 'synthetic_mule_like']
        all_accounts = list(account_info.keys())
        
        # Generate base timestamp
        end_time = datetime.now()
        start_time = end_time - timedelta(days=time_range_days)
        
        for i in range(num_transactions):
            # Generate timestamp within range
            timestamp = fake.date_time_between(start_date=start_time, end_date=end_time)
            
            # Select sender and receiver based on behavior patterns
            sender, receiver, amount, trans_type, channel = self._generate_transaction_parameters(
                account_info, normal_accounts, active_accounts, mule_accounts, all_accounts, timestamp
            )
            
            transaction = {
                'sender_account_id': sender,
                'receiver_account_id': receiver,
                'amount': amount,
                'timestamp': timestamp,
                'transaction_type': trans_type,
                'status': random.choices(TRANSACTION_STATUSES, weights=[95, 2, 2, 1])[0],
                'channel': channel,
                'reference': fake.sentence()[:50] if random.random() > 0.7 else None
            }
            transactions.append(transaction)
        
        # Sort by timestamp and insert
        transactions.sort(key=lambda x: x['timestamp'])
        
        for trans in transactions:
            self.cursor.execute(
                """INSERT INTO transactions (sender_account_id, receiver_account_id, amount, timestamp, transaction_type, status, channel, reference)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (trans['sender_account_id'], trans['receiver_account_id'], trans['amount'],
                 trans['timestamp'], trans['transaction_type'], trans['status'],
                 trans['channel'], trans['reference'])
            )
        
        self.conn.commit()
        print(f"✓ Generated {num_transactions} transactions")
        return transactions
    
    def _generate_transaction_parameters(self, account_info, normal_accounts, active_accounts, mule_accounts, all_accounts, timestamp):
        """Generate transaction parameters based on behavior patterns"""
        
        # Determine sender account type
        sender = random.choice(all_accounts)
        sender_label = account_info[sender]
        
        # Generate transaction parameters based on sender behavior
        if sender_label == 'normal':
            # Normal users: occasional, random counterparties
            receiver = random.choice([acc for acc in all_accounts if acc != sender])
            amount = round(random.uniform(500, 15000), 2)
            trans_type = random.choice(['transfer', 'payment'])
            channel = random.choice(['upi', 'neft'])
            
        elif sender_label == 'active_user':
            # Active users: frequent, regular counterparties, larger amounts
            receiver = random.choice([acc for acc in active_accounts + normal_accounts if acc != sender])
            amount = round(random.uniform(5000, 50000), 2)
            trans_type = random.choice(['transfer', 'payment'])
            channel = random.choice(['upi', 'imps', 'neft'])
            
        else:  # synthetic_mule_like
            # Mule-like patterns based on random scenario
            scenario = random.choice(['rapid_flow', 'many_counterparties', 'concentration', 'random'])
            
            if scenario == 'rapid_flow':
                # Rapid incoming then outgoing
                if random.random() > 0.5:
                    # Receiving from many - sender is random, receiver is the mule account
                    original_sender = sender
                    sender = random.choice([acc for acc in all_accounts if acc != original_sender])
                    receiver = original_sender
                else:
                    # Sending to few - sender is mule account, receiver is random
                    receiver = random.choice([acc for acc in all_accounts if acc != sender])
                amount = round(random.uniform(2000, 10000), 2)
                
            elif scenario == 'many_counterparties':
                # Many different counterparties
                receiver = random.choice([acc for acc in all_accounts if acc != sender])
                amount = round(random.uniform(1000, 8000), 2)
                
            elif scenario == 'concentration':
                # Multiple accounts to single destination
                possible_receivers = mule_accounts[:1] if mule_accounts else all_accounts
                valid_receivers = [acc for acc in possible_receivers if acc != sender]
                receiver = random.choice(valid_receivers) if valid_receivers else random.choice([acc for acc in all_accounts if acc != sender])
                amount = round(random.uniform(2000, 15000), 2)
                
            else:  # random
                receiver = random.choice([acc for acc in all_accounts if acc != sender])
                amount = round(random.uniform(500, 12000), 2)
            
            trans_type = random.choice(['transfer', 'payment'])
            channel = random.choice(['upi', 'imps'])
        
        # Final safety check to prevent self-transfers
        if sender == receiver:
            receiver = random.choice([acc for acc in all_accounts if acc != sender])
        
        return sender, receiver, amount, trans_type, channel
    
    def generate_statistics(self):
        """Generate and display database statistics"""
        print("\n" + "="*50)
        print("DATABASE STATISTICS")
        print("="*50)
        
        # Customer count
        self.cursor.execute("SELECT COUNT(*) FROM customers")
        print(f"Customers: {self.cursor.fetchone()[0]}")
        
        # Account count by type
        self.cursor.execute("SELECT account_label, COUNT(*) FROM accounts GROUP BY account_label")
        print("\nAccounts by behavior type:")
        for label, count in self.cursor.fetchall():
            print(f"  {label}: {count}")
        
        # Transaction count
        self.cursor.execute("SELECT COUNT(*) FROM transactions")
        print(f"\nTotal transactions: {self.cursor.fetchone()[0]}")
        
        # Transaction count by type
        self.cursor.execute("SELECT transaction_type, COUNT(*) FROM transactions GROUP BY transaction_type")
        print("\nTransactions by type:")
        for trans_type, count in self.cursor.fetchall():
            print(f"  {trans_type}: {count}")
        
        # Transaction count by status
        self.cursor.execute("SELECT status, COUNT(*) FROM transactions GROUP BY status")
        print("\nTransactions by status:")
        for status, count in self.cursor.fetchall():
            print(f"  {status}: {count}")
        
        # Balance statistics
        self.cursor.execute("SELECT account_label, AVG(balance), MIN(balance), MAX(balance) FROM accounts GROUP BY account_label")
        print("\nBalance statistics by behavior type:")
        for label, avg_bal, min_bal, max_bal in self.cursor.fetchall():
            print(f"  {label}:")
            print(f"    Average: ₹{avg_bal:,.2f}")
            print(f"    Min: ₹{min_bal:,.2f}")
            print(f"    Max: ₹{max_bal:,.2f}")


def main(config=None, clear_data=True):
    """Main function to generate synthetic data"""
    print("="*50)
    print("MULEGUARD SYNTHETIC DATA GENERATOR")
    print("="*50)
    
    # Use provided config or default to medium
    if config is None:
        config = MEDIUM_CONFIG
    
    # Extract configuration
    NUM_CUSTOMERS = config['num_customers']
    NUM_ACCOUNTS = config['num_accounts']
    NUM_TRANSACTIONS = config['num_transactions']
    TIME_RANGE_DAYS = config['time_range_days']
    BEHAVIOR_DISTRIBUTION = config['behavior_distribution']
    
    print(f"\nConfiguration:")
    print(f"  Customers: {NUM_CUSTOMERS}")
    print(f"  Accounts: {NUM_ACCOUNTS}")
    print(f"  Transactions: {NUM_TRANSACTIONS}")
    print(f"  Time range: {TIME_RANGE_DAYS} days")
    print(f"  Behavior distribution: {BEHAVIOR_DISTRIBUTION}")
    
    # Initialize generator
    generator = SyntheticDataGenerator(DB_PARAMS)
    
    try:
        # Connect to database
        generator.connect()
        
        # Clear existing data if requested
        if clear_data:
            print("\nClearing existing data...")
            generator.clear_existing_data()
        else:
            print("\nAppending to existing data...")
        
        # Generate customers
        print(f"\nGenerating {NUM_CUSTOMERS} customers...")
        generator.generate_customers(NUM_CUSTOMERS)
        
        # Generate accounts
        print(f"\nGenerating {NUM_ACCOUNTS} accounts...")
        generator.generate_accounts(NUM_ACCOUNTS, BEHAVIOR_DISTRIBUTION)
        
        # Generate transactions
        print(f"\nGenerating {NUM_TRANSACTIONS} transactions over {TIME_RANGE_DAYS} days...")
        generator.generate_transactions(NUM_TRANSACTIONS, None, TIME_RANGE_DAYS)
        
        # Display statistics
        generator.generate_statistics()
        
        print("\n" + "="*50)
        print("✓ SYNTHETIC DATA GENERATION COMPLETE")
        print("="*50)
        
    except Exception as e:
        print(f"\n✗ Error during generation: {e}")
        if generator.conn:
            generator.conn.rollback()
    finally:
        generator.close()


if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        config_name = sys.argv[1].lower()
        if config_name == 'small':
            main(SMALL_CONFIG)
        elif config_name == 'medium':
            main(MEDIUM_CONFIG)
        elif config_name == 'large':
            main(LARGE_CONFIG)
        elif config_name == 'production':
            main(PRODUCTION_CONFIG)
        else:
            print(f"Unknown configuration: {config_name}")
            print("Available: small, medium, large, production")
    else:
        # Default to medium configuration
        main(MEDIUM_CONFIG)