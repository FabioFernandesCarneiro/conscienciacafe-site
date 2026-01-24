#!/usr/bin/env python3
"""Sistema Web de Gestao Financeira - Consciencia Cafe."""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user
from sqlalchemy import text

from src.auth_routes import create_auth_blueprint
from src.auth_service_sqlalchemy import AuthService
from src.b2b.b2b_metrics import B2BMetrics
from src.b2b.crm_service import CRMService
from src.b2b.google_maps_client import GoogleMapsClient
from src.b2b.google_sheets_client import GoogleSheetsClient
from src.b2b.lead_enrichment import LeadEnrichmentService
from src.commission_routes import create_commission_blueprint
from src.crm_routes import create_crm_blueprint
from src.db import init_engine
from src.exchange_routes import create_exchange_blueprint
from src.legacy_routes import create_legacy_blueprint
from src.local_data_service import LocalDataService
from src.local_routes import create_local_blueprint
from src.ml_categorizer import MLCategorizer
from src.ml_routes import create_ml_blueprint
from src.models import Base
from src.orders_routes import create_orders_blueprint
from src.services.catalog_service import CatalogService
from src.services.commission_rate_service import CommissionRateService
from src.services.commission_service import CommissionService
from src.services.exchange_rate_service import ExchangeRateService
from src.services.order_service import OrderService

# ==========================
# Environment Configuration
# ==========================

load_dotenv()

# ==========================
# Database Initialization
# ==========================

engine = init_engine(os.getenv('DATABASE_URL'))
Base.metadata.create_all(engine)

# ==========================
# Flask Application
# ==========================

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')

# ==========================
# Logging Configuration
# ==========================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)
logger = logging.getLogger(__name__)

# ==========================
# Service Initialization
# ==========================

# ML categorization service
ml_categorizer = MLCategorizer()

# B2B services
google_sheets_client = GoogleSheetsClient()
b2b_metrics = B2BMetrics()

# Local data services
local_service = LocalDataService()
crm_service = CRMService()
lead_enrichment_service = LeadEnrichmentService()

# Auth and catalog services
auth_service = AuthService()
coffee_catalog_service = CatalogService()
order_service = OrderService()

# Commission and exchange rate services
commission_rate_service = CommissionRateService()
exchange_rate_service = ExchangeRateService()
commission_service = CommissionService(commission_rate_service, exchange_rate_service)

# Google Maps client (optional)
google_maps_client = None
try:
    google_maps_client = GoogleMapsClient()
except Exception as exc:
    logger.warning("Google Maps API desabilitada: %s", exc)

# B2B analytics modules (optional)
sales_analyzer = None
sales_repository = None
try:
    from src.b2b.sales_analyzer import SalesAnalyzer
    from src.b2b.sales_repository import SalesRepository

    sales_repository = SalesRepository(exchange_rate_service=exchange_rate_service)
    sales_analyzer = SalesAnalyzer(sales_repository, crm_service)
    print("Modulos B2B carregados com sucesso")
except ImportError as e:
    logger.warning("Erro ao carregar modulos B2B: %s", e)

# ==========================
# Authentication Setup
# ==========================

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id: str):
    """Load user by ID for Flask-Login."""
    try:
        return auth_service.load_user_by_id(int(user_id))
    except (TypeError, ValueError):
        return None


LOGIN_EXEMPT_ENDPOINTS = {
    'auth.login',
    'auth.logout',
    'admin_fix_sequences',
}


@app.before_request
def require_login():
    """Require login for all routes except exempt endpoints."""
    endpoint = request.endpoint
    if not endpoint:
        return None

    if endpoint.startswith('static'):
        return None
    if endpoint in LOGIN_EXEMPT_ENDPOINTS:
        return None
    if endpoint.startswith('auth.'):
        return None
    if current_user.is_authenticated:
        return None

    next_url = request.url if request.method == 'GET' else url_for('dashboard')
    return redirect(url_for('auth.login', next=next_url))


# ==========================
# Blueprint Registration
# ==========================

# Authentication
app.register_blueprint(create_auth_blueprint(auth_service))

# Orders and catalog
app.register_blueprint(
    create_orders_blueprint(
        coffee_catalog_service,
        order_service,
        crm_service,
        google_sheets_client,
        lead_enrichment_service,
        google_maps_client,
        auth_service,
    )
)

# Commissions
app.register_blueprint(
    create_commission_blueprint(commission_service, commission_rate_service)
)

# Exchange rates
app.register_blueprint(create_exchange_blueprint(exchange_rate_service))

# Local data routes
app.register_blueprint(create_local_blueprint(local_service))

# CRM and B2B dashboard
app.register_blueprint(
    create_crm_blueprint(
        crm_service,
        google_maps_client,
        lead_enrichment_service,
        sales_analyzer,
        sales_repository,
        exchange_rate_service,
        order_service,
        auth_service,
    )
)

# Legacy routes (disabled Omie integration)
app.register_blueprint(create_legacy_blueprint())

# ML intelligent suggestions
app.register_blueprint(create_ml_blueprint(ml_categorizer))


# ==========================
# Main Routes
# ==========================

@app.route('/')
def dashboard():
    """Main dashboard (B2B)."""
    return render_template('b2b_dashboard.html')


# ==========================
# Admin Routes
# ==========================

@app.route('/admin/fix-sequences')
def admin_fix_sequences():
    """Fix PostgreSQL sequences for auto-increment columns."""
    try:
        if engine.dialect.name != 'postgresql':
            return {
                'success': False,
                'error': f'This tool only works with PostgreSQL. Current dialect: {engine.dialect.name}'
            }

        tables_to_fix = [
            'coffee_products',
            'coffee_packaging_prices',
            'orders',
            'order_items',
            'crm_users',
            'crm_leads',
            'crm_interactions',
        ]

        results = []

        with engine.connect() as conn:
            for table_name in tables_to_fix:
                try:
                    sequence_name = f"{table_name}_id_seq"

                    result = conn.execute(text(f"SELECT MAX(id) FROM {table_name}"))
                    max_id = result.scalar()

                    if max_id is None:
                        max_id = 0

                    next_val = max_id + 1
                    conn.execute(text(f"SELECT setval('{sequence_name}', {next_val}, false)"))

                    result = conn.execute(text(f"SELECT last_value FROM {sequence_name}"))
                    new_val = result.scalar()

                    results.append({
                        'table': table_name,
                        'success': True,
                        'max_id': max_id,
                        'new_sequence_value': int(new_val),
                        'next_id': int(new_val)
                    })

                except Exception as e:
                    results.append({
                        'table': table_name,
                        'success': False,
                        'error': str(e)
                    })

            conn.commit()

        success_count = sum(1 for r in results if r.get('success'))

        return {
            'success': True,
            'message': f'Fixed {success_count}/{len(tables_to_fix)} sequences',
            'results': results
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# ==========================
# Application Entry Point
# ==========================

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('models', exist_ok=True)

    port = int(os.environ.get('PORT', 5002))

    print("Iniciando Sistema Web de Gestao Financeira")
    print(f"Dashboard: http://localhost:{port}")
    print(f"Extrato PJ: http://localhost:{port}/extrato-pj")
    print(f"Dashboard B2B: http://localhost:{port}/dashboard-b2b")

    is_production = os.environ.get('RAILWAY_ENVIRONMENT') is not None
    app.run(debug=not is_production, host='0.0.0.0', port=port)
