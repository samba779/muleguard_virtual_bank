# MuleGuard Virtual Bank - Project Handover

## Handover Summary

**From**: Samba (Virtual Bank, PostgreSQL, Synthetic Data Engineer)  
**To**: Bhanu (API, Behavioral Analysis, ML/Risk Model, Graph Analysis)  
**Date**: August 22, 2026  
**Project**: MuleGuard Fraud Detection Prototype

---

## What Has Been Delivered

### 1. PostgreSQL Database ✅
- **Database Name**: `muleguard_bank`
- **Tables**: customers, accounts, transactions
- **Schema**: Fully designed with proper constraints, indexes, and relationships
- **Status**: Production-ready for API integration

### 2. Synthetic Dataset ✅
- **Current Size**: Medium configuration
  - 50 customers
  - 100 accounts  
  - 1,000 transactions
- **Time Range**: 60 days of transaction data
- **Behavioral Types**: Normal (41%), Active User (39%), Mule-like (20%)
- **Quality**: Verified - no data quality issues, all constraints respected

### 3. Data Generation Tool ✅
- **Script**: `synthetic_data_generator.py`
- **Features**: Configurable scale, realistic patterns, safety checks
- **Configurations**: Small, Medium, Large, Production
- **Security**: Environment variables for credentials
- **Status**: Tested and documented

### 4. Documentation ✅
- **Database Documentation**: Complete schema, relationships, sample queries
- **Quick Reference**: Essential queries and patterns
- **Generator Documentation**: Usage instructions and configuration
- **Security Setup**: .env file, .gitignore, security best practices

---

## Database Schema Overview

### Core Tables
```
customers (1) ──────< (N) accounts (1) ──────< (N) transactions
```

### Key Design Decisions
1. **Transaction Direction**: Preserved via sender_account_id and receiver_account_id
2. **Behavior Labels**: account_label field provides ground truth for ML
3. **Self-Transfer Prevention**: Database constraint prevents sender = receiver
4. **Temporal Support**: Timestamps enable time-based analysis
5. **Graph Ready**: Easy to convert to nodes (accounts) and edges (transactions)

### Important Fields for ML/Graph Analysis
- `account_label` → Ground truth labels
- `sender_account_id` / `receiver_account_id` → Transaction direction
- `timestamp` → Temporal analysis
- `amount` → Transaction amounts
- `channel` → Transaction channel patterns

---

## Current Dataset Statistics

### Account Distribution
| Type | Count | % | Avg Balance | Avg Transactions |
|------|-------|---|-------------|------------------|
| Normal | 41 | 41% | ₹62,454 | 20.7 |
| Active User | 39 | 39% | ₹286,251 | 20.3 |
| Mule-like | 20 | 20% | ₹29,576 | 17.9 |

### Transaction Distribution
- **Total**: 1,000 transactions
- **Types**: 493 transfers, 507 payments
- **Status**: 955 completed, 21 pending, 14 failed, 10 cancelled
- **Time Range**: 60 days
- **Self-Transfers**: 0 (prevented by constraint)

---

## Behavioral Patterns

### Normal Users
- Represents everyday banking behavior
- Occasional transactions, stable counterparties
- Important for establishing baseline patterns

### Active Legitimate Users  
- High transaction frequency but legitimate
- Critical for preventing false positives
- Shows that high activity ≠ fraud

### Synthetic Mule-like Scenarios
- Test scenarios for fraud detection
- Patterns: rapid flow, many counterparties, concentration
- **Important**: These are test scenarios, NOT confirmed fraud

---

## For API Integration

### Connection Information
- **Database**: muleguard_bank
- **Host**: localhost (configurable in .env)
- **Credentials**: Stored in .env file
- **Schema**: See DATABASE_DOCUMENTATION.md

### API Development Notes
1. **Don't mix bank accounts with MuleGuard users**: Bank accounts are data being analyzed, MuleGuard users are investigators
2. **Use existing schema**: Schema designed to support ML and graph analysis requirements
3. **Respect constraints**: Self-transfer prevention, enum values, foreign keys
4. **Ground truth available**: account_label field for ML model training

### Recommended API Endpoints
- Get account information with transaction history
- Get transaction network data for graph analysis
- Query accounts by behavioral patterns
- Time-based transaction queries
- Counterparty analysis

---

## For ML/Behavioral Analysis

### Available Features
- Transaction velocity (transactions per time period)
- Transaction frequency patterns
- Incoming/outgoing ratios and amounts
- Unique counterparty counts
- Average transaction amounts
- Rapid transfer intervals
- Temporal behavior changes
- Network centrality measures

### Ground Truth Labels
- `account_label` field provides training labels
- Values: 'normal', 'active_user', 'synthetic_mule_like'
- **Important**: Synthetic scenarios, not real fraud cases

### Feature Engineering Opportunities
- Time-based features (hour of day, day of week)
- Amount-based features (ratios, averages, ranges)
- Network features (centrality, clustering, path lengths)
- Behavioral change features (activity ratios, pattern shifts)

---

## For Graph Analysis

### Graph Construction
- **Nodes**: Accounts (from accounts table)
- **Edges**: Transactions (from transactions table)
- **Edge Direction**: sender → receiver
- **Edge Weights**: Transaction count, total amount

### Network Analysis Support
- Transaction direction preserved
- Easy to extract account-to-account relationships
- Supports centrality, clustering, path analysis
- Temporal network analysis possible via timestamps

### Sample Graph Query
```sql
SELECT 
    s.account_id as source,
    r.account_id as target,
    COUNT(*) as weight,
    SUM(t.amount) as total_amount
FROM transactions t
JOIN accounts s ON t.sender_account_id = s.account_id
JOIN accounts r ON t.receiver_account_id = r.account_id
GROUP BY s.account_id, r.account_id;
```

---

## Files Delivered

### Database Files
- `.env` - Database credentials (not in git)
- `.env.example` - Credential template
- `.gitignore` - Git ignore rules

### Generator Files  
- `synthetic_data_generator.py` - Main data generation script
- `generator_config.py` - Configuration options
- `test_generator.py` - Test script

### Documentation Files
- `DATABASE_DOCUMENTATION.md` - Complete database documentation
- `QUICK_REFERENCE.md` - Essential queries and reference
- `GENERATOR_README.md` - Generator usage documentation
- `PROJECT_HANDOVER.md` - This handover document

---

## Security and Best Practices

### Security Status ✅
- Database credentials in .env file (not hardcoded)
- .gitignore prevents credential commits
- No git repository initialized yet (clean state)
- .env.example provided for other developers

### Best Practices Applied
- Synthetic data only (no real financial information)
- Proper database constraints and validation
- Environment variables for sensitive data
- Comprehensive error handling
- Safety checks in data generation

---

## Scalability Options

### Current Dataset
- Medium configuration: 1,000 transactions
- Suitable for initial API and ML development

### Scaling Options
```bash
# Large dataset: 10,000 transactions
python synthetic_data_generator.py large

# Production dataset: 100,000 transactions  
python synthetic_data_generator.py production
```

### Custom Scaling
- Edit `generator_config.py` for custom configurations
- Supports up to 100,000+ transactions
- Time range configurable (30-180 days)

---

## Known Limitations

### Current Limitations
- No geographic location data
- No device information
- Limited transaction types (transfer, payment, deposit, withdrawal)
- Synthetic behavioral patterns (not based on real fraud cases)
- No customer demographics beyond basic info

### Future Enhancement Opportunities
- Add location data for geographic analysis
- Include device fingerprinting
- Expand transaction categories
- Add merchant information
- Implement seasonal patterns
- Add customer segmentation data

---

## Next Steps for Bhanu

### Immediate Tasks
1. **Review Database Documentation**: Understand schema and relationships
2. **Test Database Connection**: Verify .env configuration works
3. **Explore Sample Queries**: Run queries from DATABASE_DOCUMENTATION.md
4. **API Design**: Plan API endpoints based on available data
5. **ML Feature Planning**: Identify features for behavioral analysis

### Integration Tasks
1. **API Development**: Build REST API for database access
2. **Behavioral Analysis**: Implement transaction pattern analysis
3. **ML Model Development**: Train models using account_label as ground truth
4. **Graph Analysis**: Implement network analysis algorithms
5. **Explainability**: Add explanation generation for risk scores

### Coordination Points
- **Samba**: Available for database questions and data generation
- **Narayana**: Project requirements and overall coordination
- **Samuel**: Frontend integration later in project

---

## Questions and Support

### Database Questions (Samba)
- Schema design and relationships
- Data generation and scaling
- Database performance and optimization
- Synthetic data quality

### Project Coordination (Narayana)
- Overall project requirements
- Integration between components
- Presentation and documentation

### Frontend Integration (Samuel - Later Phase)
- Dashboard requirements
- Data visualization needs
- API endpoint specifications

---

## Success Criteria

### Database Handover Success ✅
- [x] PostgreSQL database created and operational
- [x] Schema designed and implemented
- [x] Synthetic dataset generated and validated
- [x] Data generator functional and documented
- [x] Security best practices applied
- [x] Comprehensive documentation provided
- [x] Ready for API integration

### Next Phase Success (Bhanu)
- [ ] API successfully connects to database
- [ ] Behavioral analysis algorithms implemented
- [ ] ML model trained on synthetic data
- [ ] Graph analysis functional
- [ ] Risk scoring system operational
- [ ] Explainability features working

---

## Project Context

### MuleGuard Overview
- **Purpose**: Student-level banking fraud/mule-account detection prototype
- **Approach**: Analyze account behavior over time and transaction networks
- **Output**: Risk indicators, scores, explanations for bank investigators
- **Important**: Does NOT automatically declare accounts fraudulent

### Team Responsibilities
- **Narayana**: Project concept, requirements, documentation, presentation
- **Samba**: Virtual Bank, PostgreSQL, synthetic dataset (COMPLETED)
- **Bhanu**: API, behavioral analysis, ML/risk model, graph analysis (CURRENT)
- **Samuel**: Frontend, dashboard, UI (FUTURE)

### Architecture
```
Virtual Bank Data → PostgreSQL → Backend API → MuleGuard Analysis → Dashboard
                                   ↓
                            (Behavioral ML + Graph Analysis)
```

---

## Conclusion

The Virtual Bank database and synthetic dataset are complete and ready for API integration. The schema is designed to support the behavioral analysis, ML modeling, and graph analysis requirements. All security best practices have been applied, and comprehensive documentation is provided.

**Database Phase**: ✅ COMPLETE  
**Handover Status**: ✅ READY  
**Next Phase**: API/ML/Graph Analysis (Bhanu)

---

**Handover Document Version**: 1.0  
**Date**: August 22, 2026  
**Database Status**: Production Ready  
**Dataset Status**: Medium Configuration (1,000 transactions)