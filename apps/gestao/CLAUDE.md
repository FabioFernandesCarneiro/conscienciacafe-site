# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Intelligent bank reconciliation system for Consciência Café business that integrates with Omie ERP, uses machine learning for transaction categorization, and provides a web dashboard for financial management.

## Technology Stack

- **Backend**: Python 3.8+ with Flask web framework
- **ML/Data**: scikit-learn (TF-IDF + Naive Bayes), pandas, numpy
- **Banking**: ofxparse for OFX bank file processing, `omieapi` library for Omie ERP
- **External APIs**: Omie ERP integration, Google Sheets/Maps APIs
- **Authentication**: gspread with google-auth for Google services
- **Database**: SQLite for ML learning data and local storage

## Development Setup

```bash
# Initial setup
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Configure API credentials

# Run applications
python main.py           # CLI reconciliation system
python app.py            # Web application (port 5001)
./run.sh                # CLI with venv activation
```

## Core Architecture

### Main Entry Points

- **`main.py`** - CLI reconciliation system with intelligent OFX account type detection
- **`app.py`** - Flask web application (78KB+) with dashboard, APIs, and PJ statement viewer
- **`smart_reconciliation_extrato.py`** - Advanced reconciliation engine using Omie's Extrato API
- **`main_smart.py`** - Alternative smart reconciliation entry point

### Core Engine Components

**OFX Processing & Detection**:
- `src/ofx_parser.py` - OFX bank file parser and transaction extractor
- `src/ofx_detector.py` - Automatic bank account type detection (checking vs credit card)

**Omie Integration**:
- `src/omie_client.py` - Comprehensive Omie ERP API client using official `omieapi` library
- Account ID mapping: System IDs (8=checking, 9=credit) → Omie internal IDs (2103553430)
- Handles multiple API endpoints: conta corrente, contas a receber/pagar, extrato

**Intelligence & Reconciliation**:
- `src/ml_categorizer.py` - ML categorization with TF-IDF vectorization + Naive Bayes
- `src/reconciliation_engine.py` - Main reconciliation logic and duplicate detection
- `src/smart_reconciliation.py` - Enhanced reconciliation with smart search algorithms

**Data Management**:
- `src/database_manager.py` - SQLite operations and schema management
- `src/local_data_service.py` - Local data persistence and caching
- `src/account_manager.py` - Account configuration and mapping

**B2B Analytics Module** (`src/b2b/`):
- `google_sheets_client.py` - Google Sheets integration for sales data
- `sales_analyzer.py` - B2B sales analysis and metrics
- `client_manager.py` - Client/customer management
- `b2b_metrics.py` - Metrics calculation (LTV, churn risk, ticket médio)
- `crm_service.py` - CRM functionality
- `google_maps_client.py` - Location services integration

### Web Application (Flask)

**Routes & Views**:
- `/` - Dashboard with financial overview and status cards
- `/extrato-pj` - Business account statements with advanced filtering
- `/dashboard-b2b` - B2B analytics dashboard
- `/orders` - Gestão interna de pedidos B2B
- `/orders/coffees` - Catálogo de cafés e preços por embalagem
- `/api/contas-disponiveis` - List available accounts
- `/api/extrato-conta-corrente` - Account statement API
- `/api/b2b/*` - B2B analytics APIs

**Templates** (`templates/`):
- `base.html` - Base template with sidebar navigation
- `dashboard.html` - Main dashboard
- `extrato_pj.html` - PJ statement viewer
- `b2b_dashboard.html` - B2B analytics interface

## ML-Powered Reconciliation Flow

1. **OFX Analysis**: Automatic detection of Nubank PJ account types (ID 8=checking, ID 9=credit card)
2. **Transaction Parsing**: Extract, clean and normalize transaction data from OFX files
3. **Duplicate Detection**: Smart search in existing Omie entries to prevent duplicates
4. **ML Categorization**: TF-IDF vectorization + Naive Bayes to predict transaction categories
5. **Confidence-Based Processing**:
   - >70% confidence: Auto-create entries
   - <70% confidence: Manual review required
6. **Learning Loop**: Store manual corrections in `data/learning_data.db` to improve future predictions

## Key Commands

### CLI Reconciliation
```bash
python main.py                     # Interactive OFX reconciliation
./run.sh                          # CLI with virtual environment
```

### Web Application
```bash
python app.py                      # Start web server on port 5001
# Access: http://localhost:5001
```

### Machine Learning & Training
```bash
python historical_learning_extrato.py      # Train ML models with historical data
python optimized_historical_learning.py    # Optimized historical learning
```

### Data Migration
```bash
python omie_migration.py                   # Full Omie data migration
python run_full_migration_2023.py          # Historical data from 2023
./start_migration.sh                      # Background migration with logs
python background_migration.py status      # Check migration status
python background_migration.py logs        # View migration logs
```

### Testing & Debugging
```bash
python test_omie_api_contas.py             # Test Omie API connectivity
python test_validation_100_percent.py      # Validate reconciliation accuracy
python test_enhanced_search.py             # Test search algorithms
python debug_credit_matching.py            # Debug credit card matching
```

## Environment Configuration

Required environment variables in `.env`:

```bash
# Omie ERP API (required)
OMIE_APP_KEY=your_app_key
OMIE_APP_SECRET=your_app_secret

# Google Services (optional, for B2B features)
GOOGLE_CREDENTIALS_FILE=path/to/credentials.json
GOOGLE_SPREADSHEET_KEY=spreadsheet_id
GOOGLE_MAPS_API_KEY=maps_api_key

# Flask (optional, has defaults)
FLASK_SECRET_KEY=your_secret_key
FLASK_ENV=development
```

## Important Data Locations

- `Consciencia_Cafe/data/learning_data.db` - SQLite database for ML training data and manual corrections
- `Consciencia_Cafe/data/local_financeiro.db` - Local financial data cache and processing results
- Tabelas `coffee_products`, `coffee_packaging_prices`, `orders`, `order_items` suportam catálogo interno de cafés e pedidos B2B
- `models/categorizer_model.pkl` - Trained scikit-learn model for transaction categorization
- `Consciencia_Cafe/data/migration.log` - Migration process logs
- `Consciencia_Cafe/data/migration_output.log` - Background migration output

## Architecture Patterns

**Account Management**:
- System uses abstract IDs (8, 9) that map to Omie internal account IDs
- Mapping handled in `OmieClient.set_account_id()` method
- Nubank PJ: checking (8) and credit (9) both use same Omie ID (2103553430)

**API Abstraction**:
- `OmieClient` wraps the official `omieapi` library
- Provides error handling and retries
- Centralizes account ID management

**ML Pipeline**:
- Training data stored in SQLite
- Models serialized with pickle in `models/`
- Incremental learning from manual corrections
- TF-IDF features + Naive Bayes classifier

**Caching Strategy**:
- In-memory cache for account lists (1 hour TTL)
- SQLite for persistent caching
- Reduces API calls to Omie

## Virtual Environment

The project uses a Python virtual environment located in `venv/`. Always activate it before running commands:

```bash
source venv/bin/activate
```

## Notes on Package Management

- macOS uses externally-managed Python environment
- Must use virtual environment for package installation
- To upgrade packages: `source venv/bin/activate && pip install --upgrade package_name`
- Never use `--break-system-packages` flag
