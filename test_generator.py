"""
Test the synthetic data generator with small dataset
"""

import sys
sys.path.insert(0, 'C:\\Users\\samba')

# Import the generator
from synthetic_data_generator import SyntheticDataGenerator, DB_PARAMS

# Test configuration
NUM_CUSTOMERS = 10
NUM_ACCOUNTS = 10
NUM_TRANSACTIONS = 50
TIME_RANGE_DAYS = 30

BEHAVIOR_DISTRIBUTION = {
    'types': ['normal', 'active_user', 'synthetic_mule_like'],
    'weights': [0.4, 0.3, 0.3]  # 40% normal, 30% active, 30% mule-like for testing
}

def test_generator():
    print("="*50)
    print("TESTING SYNTHETIC DATA GENERATOR")
    print("="*50)
    
    generator = SyntheticDataGenerator(DB_PARAMS)
    
    try:
        generator.connect()
        
        # Clear existing data
        print("\nClearing existing data...")
        generator.clear_existing_data()
        
        # Generate test data
        print(f"\nGenerating {NUM_CUSTOMERS} customers...")
        generator.generate_customers(NUM_CUSTOMERS)
        
        print(f"\nGenerating {NUM_ACCOUNTS} accounts...")
        generator.generate_accounts(NUM_ACCOUNTS, BEHAVIOR_DISTRIBUTION)
        
        print(f"\nGenerating {NUM_TRANSACTIONS} transactions...")
        generator.generate_transactions(NUM_TRANSACTIONS, None, TIME_RANGE_DAYS)
        
        # Display statistics
        generator.generate_statistics()
        
        print("\n" + "="*50)
        print("✓ TEST COMPLETE")
        print("="*50)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        if generator.conn:
            generator.conn.rollback()
    finally:
        generator.close()

if __name__ == "__main__":
    test_generator()