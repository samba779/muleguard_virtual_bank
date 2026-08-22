"""
Configuration file for synthetic data generator
"""

# Small test configuration
SMALL_CONFIG = {
    'num_customers': 10,
    'num_accounts': 10,
    'num_transactions': 50,
    'time_range_days': 30,
    'behavior_distribution': {
        'types': ['normal', 'active_user', 'synthetic_mule_like'],
        'weights': [0.4, 0.3, 0.3]
    }
}

# Medium configuration
MEDIUM_CONFIG = {
    'num_customers': 50,
    'num_accounts': 100,
    'num_transactions': 1000,
    'time_range_days': 60,
    'behavior_distribution': {
        'types': ['normal', 'active_user', 'synthetic_mule_like'],
        'weights': [0.5, 0.3, 0.2]
    }
}

# Large configuration
LARGE_CONFIG = {
    'num_customers': 200,
    'num_accounts': 500,
    'num_transactions': 10000,
    'time_range_days': 90,
    'behavior_distribution': {
        'types': ['normal', 'active_user', 'synthetic_mule_like'],
        'weights': [0.6, 0.25, 0.15]
    }
}

# Production configuration
PRODUCTION_CONFIG = {
    'num_customers': 1000,
    'num_accounts': 2500,
    'num_transactions': 100000,
    'time_range_days': 180,
    'behavior_distribution': {
        'types': ['normal', 'active_user', 'synthetic_mule_like'],
        'weights': [0.7, 0.2, 0.1]
    }
}