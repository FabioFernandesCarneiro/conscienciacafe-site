#!/usr/bin/env python3
"""
Local Data Service - Camada de Serviço para Dados Locais
Suporta SQLite legado e SQLAlchemy (PostgreSQL/Railway) de forma transparente.
"""

from __future__ import annotations

import json
import locale
import os
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any, Optional

from sqlalchemy import case, func

from src.database_manager import DatabaseManager
from src.db import session_scope
from src.models import Account, Category, Client, Transaction, ImportBatch


class LocalDataService:
    def __init__(self, db_path: Optional[str] = None, use_sqlalchemy: Optional[bool] = None):
        if use_sqlalchemy is None:
            use_sqlalchemy = bool(os.getenv('DATABASE_URL'))

        self.use_sqlalchemy = use_sqlalchemy
        self.db_path = db_path
        self.db = None if self.use_sqlalchemy else DatabaseManager(db_path)

        # Configurar locale brasileiro para formatação
        try:
            locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
        except Exception:
            try:
                locale.setlocale(locale.LC_ALL, 'pt_BR')
            except Exception:
                pass  # Usar locale padrão se brasileiro não estiver disponível

    # -------------------------------------------------------------------------
    # Contas
    # -------------------------------------------------------------------------

    def get_available_accounts(self) -> List[Dict[str, Any]]:
        if not self.use_sqlalchemy:
            return self._get_available_accounts_sqlite()
        return self._get_available_accounts_sqlalchemy()

    def _get_available_accounts_sqlite(self) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        try:
            cursor = conn.execute(
                '''
                SELECT id, omie_id, name, type, bank_name, balance, active
                FROM accounts
                ORDER BY active DESC, name
                '''
            )

            accounts = []
            for row in cursor.fetchall():
                accounts.append({
                    'id': row['omie_id'],
                    'nome': row['name'] or f"Conta {row['omie_id']}",
                    'tipo': row['type'],
                    'banco': row['bank_name'],
                    'saldo': float(row['balance']) if row['balance'] else 0.0,
                    'ativo': bool(row['active']),
                    'local_id': row['id'],
                })
            return accounts
        finally:
            conn.close()

    def _get_available_accounts_sqlalchemy(self) -> List[Dict[str, Any]]:
        with session_scope() as session:
            accounts = (
                session.query(Account)
                .order_by(Account.active.desc(), Account.name)
                .all()
            )
            result: List[Dict[str, Any]] = []
            for account in accounts:
                result.append({
                    'id': account.omie_id or account.id,
                    'nome': account.name or f"Conta {account.id}",
                    'tipo': account.type,
                    'banco': account.bank_name,
                    'saldo': self._to_float(account.balance),
                    'ativo': bool(account.active),
                    'local_id': account.id,
                })
            return result

    # -------------------------------------------------------------------------
    # Extrato
    # -------------------------------------------------------------------------

    def get_account_statement(
        self,
        account_id: int,
        start_date: str,
        end_date: str,
        page: int = 1,
        per_page: int = 1000
    ) -> Dict[str, Any]:
        if not self.use_sqlalchemy:
            return self._get_account_statement_sqlite(account_id, start_date, end_date, page, per_page)
        return self._get_account_statement_sqlalchemy(account_id, start_date, end_date, page, per_page)

    def _get_account_statement_sqlite(
        self,
        account_id: int,
        start_date: str,
        end_date: str,
        page: int,
        per_page: int
    ) -> Dict[str, Any]:
        try:
            start_date_obj = datetime.strptime(start_date, '%d/%m/%Y').date() if start_date else None
            end_date_obj = datetime.strptime(end_date, '%d/%m/%Y').date() if end_date else None
        except ValueError:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
            except ValueError:
                start_date_obj = None
                end_date_obj = None

        local_account = self.db.get_account_by_omie_id(account_id)
        if not local_account:
            return {
                'success': False,
                'error': f'Conta {account_id} não encontrada',
                'extrato': [],
                'resumo': {}
            }

        transactions = self.db.get_transactions(
            account_id=local_account['id'],
            start_date=start_date_obj,
            end_date=end_date_obj,
            limit=per_page
        )

        extrato: List[Dict[str, Any]] = []
        total_creditos = 0.0
        total_debitos = 0.0

        for trans in transactions:
            trans_date = trans['date']
            if isinstance(trans_date, str):
                trans_date = datetime.strptime(trans_date, '%Y-%m-%d').date()
            formatted_date = trans_date.strftime('%d/%m/%Y')

            amount = float(trans['amount'])
            if trans['type'] == 'credit':
                total_creditos += amount
            else:
                total_debitos += amount

            reconciled = trans['reconciled_status'] == 'reconciled'
            extrato.append({
                'codigo': trans['omie_code'] or trans['id'],
                'data': formatted_date,
                'descricao': trans['description'],
                'categoria': trans['category_name'] or 'Sem Categoria',
                'categoria_codigo': trans['category_id'],
                'cliente': trans['client_name'] or '',
                'tipo': 'Crédito' if trans['type'] == 'credit' else 'Débito',
                'valor': amount,
                'valor_formatado': self.format_currency(amount),
                'saldo': float(trans['balance']) if trans['balance'] else 0.0,
                'saldo_formatado': self.format_currency(float(trans['balance']) if trans['balance'] else 0.0),
                'documento': trans['document_number'] or '',
                'conciliado': reconciled,
                'data_conciliacao': trans['reconciled_at'] if reconciled else None,
                'natureza': 'R' if trans['type'] == 'credit' else 'D',
                'tipo_documento': 'Transferência',
                'origem': 'Local'
            })

        saldo_periodo = total_creditos - total_debitos
        resumo = {
            'total_creditos': total_creditos,
            'total_creditos_formatado': self.format_currency(total_creditos),
            'total_debitos': total_debitos,
            'total_debitos_formatado': self.format_currency(total_debitos),
            'saldo_periodo': saldo_periodo,
            'saldo_periodo_formatado': self.format_currency(saldo_periodo),
            'total_lancamentos': len(extrato),
            'periodo': f"{start_date} a {end_date}" if start_date and end_date else "Período completo"
        }

        conta_info = {
            'id': account_id,
            'nome': local_account['name'],
            'tipo': local_account['type'],
            'banco': local_account['bank_name']
        }

        return {
            'success': True,
            'extrato': extrato,
            'resumo': resumo,
            'conta_info': conta_info,
            'total_registros': len(extrato),
            'pagina_atual': page,
            'fonte': 'local_database'
        }

    def _get_account_statement_sqlalchemy(
        self,
        account_id: int,
        start_date: str,
        end_date: str,
        page: int,
        per_page: int
    ) -> Dict[str, Any]:
        start_date_obj = self._parse_input_date(start_date)
        end_date_obj = self._parse_input_date(end_date)

        with session_scope() as session:
            account = (
                session.query(Account)
                .filter(Account.omie_id == account_id)
                .first()
            )
            if not account:
                account = session.get(Account, account_id)

            if not account:
                return {
                    'success': False,
                    'error': f'Conta {account_id} não encontrada',
                    'extrato': [],
                    'resumo': {}
                }

            query = (
                session.query(Transaction, Category, Client)
                .outerjoin(Category, Transaction.category_id == Category.id)
                .outerjoin(Client, Transaction.client_id == Client.id)
                .filter(Transaction.account_id == account.id)
            )

            if start_date_obj:
                query = query.filter(Transaction.date >= start_date_obj)
            if end_date_obj:
                query = query.filter(Transaction.date <= end_date_obj)

            transactions = (
                query
                .order_by(Transaction.date.desc(), Transaction.id.desc())
                .limit(per_page)
                .all()
            )

            extrato: List[Dict[str, Any]] = []
            total_creditos = 0.0
            total_debitos = 0.0

            for txn, category, client in transactions:
                trans_date = txn.date
                if isinstance(trans_date, datetime):
                    trans_date = trans_date.date()
                formatted_date = trans_date.strftime('%d/%m/%Y') if trans_date else ''

                amount = self._to_float(txn.amount)
                if txn.type == 'credit':
                    total_creditos += amount
                else:
                    total_debitos += amount

                balance = self._to_float(txn.balance)
                reconciled = txn.reconciled_status == 'reconciled'
                extrato.append({
                    'codigo': txn.omie_code or txn.id,
                    'data': formatted_date,
                    'descricao': txn.description,
                    'categoria': category.name if category else 'Sem Categoria',
                    'categoria_codigo': txn.category_id,
                    'cliente': client.name if client else '',
                    'tipo': 'Crédito' if txn.type == 'credit' else 'Débito',
                    'valor': amount,
                    'valor_formatado': self.format_currency(amount),
                    'saldo': balance,
                    'saldo_formatado': self.format_currency(balance),
                    'documento': txn.document_number or '',
                    'conciliado': reconciled,
                    'data_conciliacao': txn.reconciled_at.isoformat() if reconciled and txn.reconciled_at else None,
                    'natureza': 'R' if txn.type == 'credit' else 'D',
                    'tipo_documento': 'Transferência',
                    'origem': 'Railway/PostgreSQL'
                })

            saldo_periodo = total_creditos - total_debitos
            resumo = {
                'total_creditos': total_creditos,
                'total_creditos_formatado': self.format_currency(total_creditos),
                'total_debitos': total_debitos,
                'total_debitos_formatado': self.format_currency(total_debitos),
                'saldo_periodo': saldo_periodo,
                'saldo_periodo_formatado': self.format_currency(saldo_periodo),
                'total_lancamentos': len(extrato),
                'periodo': f"{start_date} a {end_date}" if start_date and end_date else "Período completo"
            }

            conta_info = {
                'id': account.omie_id or account.id,
                'nome': account.name,
                'tipo': account.type,
                'banco': account.bank_name
            }

            return {
                'success': True,
                'extrato': extrato,
                'resumo': resumo,
                'conta_info': conta_info,
                'total_registros': len(extrato),
                'pagina_atual': page,
                'fonte': 'postgres_database'
            }

    # -------------------------------------------------------------------------
    # Catálogos (categorias, clientes)
    # -------------------------------------------------------------------------

    def get_categories(self) -> List[Dict[str, Any]]:
        if not self.use_sqlalchemy:
            return self._get_categories_sqlite()
        return self._get_categories_sqlalchemy()

    def _get_categories_sqlite(self) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        try:
            cursor = conn.execute(
                '''
                SELECT id, omie_code, name, type, active
                FROM categories
                WHERE active = 1
                ORDER BY type, name
                '''
            )
            categories = []
            for row in cursor.fetchall():
                categories.append({
                    'codigo': row['omie_code'] or str(row['id']),
                    'descricao': row['name'],
                    'tipo': row['type'],
                    'local_id': row['id']
                })
            return categories
        finally:
            conn.close()

    def _get_categories_sqlalchemy(self) -> List[Dict[str, Any]]:
        with session_scope() as session:
            categories = (
                session.query(Category)
                .filter(Category.active.is_(True))
                .order_by(Category.type, Category.name)
                .all()
            )
            result: List[Dict[str, Any]] = []
            for category in categories:
                result.append({
                    'codigo': category.omie_code or str(category.id),
                    'descricao': category.name,
                    'tipo': category.type,
                    'local_id': category.id
                })
            return result

    def get_clients_suppliers(self) -> List[Dict[str, Any]]:
        if not self.use_sqlalchemy:
            return self._get_clients_suppliers_sqlite()
        return self._get_clients_suppliers_sqlalchemy()

    def _get_clients_suppliers_sqlite(self) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        try:
            cursor = conn.execute(
                '''
                SELECT id, omie_id, name, type, email, phone, active
                FROM clients
                WHERE active = 1
                ORDER BY type, name
                '''
            )
            clients = []
            for row in cursor.fetchall():
                clients.append({
                    'codigo': row['omie_id'] or row['id'],
                    'nome': row['name'],
                    'tipo': row['type'],
                    'email': row['email'],
                    'telefone': row['phone'],
                    'local_id': row['id']
                })
            return clients
        finally:
            conn.close()

    def _get_clients_suppliers_sqlalchemy(self) -> List[Dict[str, Any]]:
        with session_scope() as session:
            clients = (
                session.query(Client)
                .filter(Client.active.is_(True))
                .order_by(Client.type, Client.name)
                .all()
            )
            result: List[Dict[str, Any]] = []
            for client in clients:
                result.append({
                    'codigo': client.omie_id or client.id,
                    'nome': client.name,
                    'tipo': client.type,
                    'email': client.email,
                    'telefone': client.phone,
                    'local_id': client.id
                })
            return result

    # -------------------------------------------------------------------------
    # Estatísticas e Migração
    # -------------------------------------------------------------------------

    def get_database_statistics(self) -> Dict[str, Any]:
        if not self.use_sqlalchemy:
            stats = self.db.get_statistics()
        else:
            stats = self._get_statistics_sqlalchemy()

        stats['data_source'] = 'postgres_database' if self.use_sqlalchemy else 'local_database'
        stats['last_migration'] = self.get_last_migration_info()
        return stats

    def _get_statistics_sqlalchemy(self) -> Dict[str, Any]:
        with session_scope() as session:
            stats: Dict[str, Any] = {}
            stats['total_accounts'] = (
                session.query(func.count(Account.id))
                .filter(Account.active.is_(True))
                .scalar() or 0
            )
            stats['total_categories'] = (
                session.query(func.count(Category.id))
                .filter(Category.active.is_(True))
                .scalar() or 0
            )
            stats['total_clients'] = (
                session.query(func.count(Client.id))
                .filter(Client.active.is_(True))
                .scalar() or 0
            )
            stats['total_transactions'] = session.query(func.count(Transaction.id)).scalar() or 0

            min_date, max_date = session.query(
                func.min(Transaction.date),
                func.max(Transaction.date)
            ).one()
            stats['date_range'] = {
                'start': min_date.isoformat() if min_date else None,
                'end': max_date.isoformat() if max_date else None
            }

            recon_rows = (
                session.query(Transaction.reconciled_status, func.count(Transaction.id))
                .group_by(Transaction.reconciled_status)
                .all()
            )
            stats['reconciliation_status'] = {
                (status or 'pending'): count for status, count in recon_rows
            }
            return stats

    def get_last_migration_info(self) -> Dict[str, Any]:
        if not self.use_sqlalchemy:
            return self._get_last_migration_info_sqlite()
        return self._get_last_migration_info_sqlalchemy()

    def _get_last_migration_info_sqlite(self) -> Dict[str, Any]:
        conn = self.db.get_connection()
        try:
            cursor = conn.execute(
                '''
                SELECT source, import_date, total_records, successful_records, status, metadata
                FROM import_batches
                ORDER BY import_date DESC
                LIMIT 1
                '''
            )
            row = cursor.fetchone()
            if not row:
                return {'status': 'no_migration_found'}
            metadata = json.loads(row['metadata']) if row['metadata'] else {}
            return {
                'source': row['source'],
                'date': row['import_date'],
                'total_records': row['total_records'],
                'successful_records': row['successful_records'],
                'status': row['status'],
                'metadata': metadata
            }
        finally:
            conn.close()

    def _get_last_migration_info_sqlalchemy(self) -> Dict[str, Any]:
        with session_scope() as session:
            batch = (
                session.query(ImportBatch)
                .order_by(ImportBatch.import_date.desc())
                .first()
            )
            if not batch:
                return {'status': 'no_migration_found'}
            metadata = json.loads(batch.metadata_json) if batch.metadata_json else {}
            return {
                'source': batch.source,
                'date': batch.import_date.isoformat() if batch.import_date else None,
                'total_records': batch.total_records,
                'successful_records': batch.successful_records,
                'status': batch.status,
                'metadata': metadata
            }

    # -------------------------------------------------------------------------
    # Utilidades
    # -------------------------------------------------------------------------

    def format_currency(self, value: float) -> str:
        try:
            return locale.currency(value, grouping=True, symbol='R$')
        except Exception:
            return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    def search_transactions(self, query: str, account_id: int = None, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.use_sqlalchemy:
            return self._search_transactions_sqlite(query, account_id, limit)
        return self._search_transactions_sqlalchemy(query, account_id, limit)

    def _search_transactions_sqlite(self, query: str, account_id: int, limit: int) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        try:
            sql = '''
                SELECT t.*, a.name as account_name, c.name as category_name, cl.name as client_name
                FROM transactions t
                LEFT JOIN accounts a ON t.account_id = a.id
                LEFT JOIN categories c ON t.category_id = c.id
                LEFT JOIN clients cl ON t.client_id = cl.id
                WHERE t.description LIKE ?
            '''
            params = [f'%{query}%']

            if account_id:
                account = self.db.get_account_by_omie_id(account_id)
                if account:
                    sql += ' AND t.account_id = ?'
                    params.append(account['id'])

            sql += ' ORDER BY t.date DESC LIMIT ?'
            params.append(limit)

            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def _search_transactions_sqlalchemy(self, query: str, account_id: int, limit: int) -> List[Dict[str, Any]]:
        pattern = f"%{query}%"
        with session_scope() as session:
            txn_query = (
                session.query(Transaction, Account, Category, Client)
                .join(Account, Transaction.account_id == Account.id)
                .outerjoin(Category, Transaction.category_id == Category.id)
                .outerjoin(Client, Transaction.client_id == Client.id)
                .filter(Transaction.description.ilike(pattern))
            )

            if account_id:
                account = (
                    session.query(Account)
                    .filter(Account.omie_id == account_id)
                    .first()
                )
                if account:
                    txn_query = txn_query.filter(Transaction.account_id == account.id)
                else:
                    txn_query = txn_query.filter(False)  # Conta inexistente => resultado vazio

            rows = (
                txn_query
                .order_by(Transaction.date.desc(), Transaction.id.desc())
                .limit(limit)
                .all()
            )

            results: List[Dict[str, Any]] = []
            for txn, account, category, client in rows:
                results.append({
                    'id': txn.id,
                    'account_id': txn.account_id,
                    'date': txn.date.isoformat() if txn.date else None,
                    'description': txn.description,
                    'amount': self._to_float(txn.amount),
                    'type': txn.type,
                    'balance': self._to_float(txn.balance),
                    'category_id': txn.category_id,
                    'client_id': txn.client_id,
                    'omie_code': txn.omie_code,
                    'document_number': txn.document_number,
                    'reconciled_status': txn.reconciled_status,
                    'reconciled_at': txn.reconciled_at.isoformat() if txn.reconciled_at else None,
                    'account_name': account.name if account else None,
                    'category_name': category.name if category else None,
                    'client_name': client.name if client else None,
                })
            return results

    def get_monthly_summary(self, year: int, account_id: int = None) -> List[Dict[str, Any]]:
        if not self.use_sqlalchemy:
            return self._get_monthly_summary_sqlite(year, account_id)
        return self._get_monthly_summary_sqlalchemy(year, account_id)

    def _get_monthly_summary_sqlite(self, year: int, account_id: int) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        try:
            sql = '''
                SELECT
                    strftime('%m', date) as month,
                    strftime('%Y', date) as year,
                    SUM(CASE WHEN type = 'credit' THEN amount ELSE 0 END) as total_credits,
                    SUM(CASE WHEN type = 'debit' THEN amount ELSE 0 END) as total_debits,
                    COUNT(*) as total_transactions
                FROM transactions t
                WHERE strftime('%Y', date) = ?
            '''
            params = [str(year)]

            if account_id:
                account = self.db.get_account_by_omie_id(account_id)
                if account:
                    sql += ' AND t.account_id = ?'
                    params.append(account['id'])

            sql += ' GROUP BY strftime(\'%Y-%m\', date) ORDER BY month'

            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def _get_monthly_summary_sqlalchemy(self, year: int, account_id: int) -> List[Dict[str, Any]]:
        year_value = int(year)
        with session_scope() as session:
            txn_query = session.query(
                func.extract('year', Transaction.date).label('year'),
                func.extract('month', Transaction.date).label('month'),
                func.sum(case((Transaction.type == 'credit', Transaction.amount), else_=0)).label('total_credits'),
                func.sum(case((Transaction.type == 'debit', Transaction.amount), else_=0)).label('total_debits'),
                func.count(Transaction.id).label('total_transactions'),
            ).filter(func.extract('year', Transaction.date) == year_value)

            if account_id:
                account = (
                    session.query(Account)
                    .filter(Account.omie_id == account_id)
                    .first()
                )
                if not account:
                    return []
                txn_query = txn_query.filter(Transaction.account_id == account.id)

            rows = (
                txn_query
                .group_by(func.extract('year', Transaction.date), func.extract('month', Transaction.date))
                .order_by(func.extract('month', Transaction.date))
                .all()
            )

            summary: List[Dict[str, Any]] = []
            for row in rows:
                month_number = int(row.month)
                summary.append({
                    'month': f"{month_number:02d}",
                    'year': str(int(row.year)),
                    'total_credits': self._to_float(row.total_credits),
                    'total_debits': self._to_float(row.total_debits),
                    'total_transactions': int(row.total_transactions),
                })
            return summary

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _to_float(value: Any) -> float:
        if value is None:
            return 0.0
        if isinstance(value, Decimal):
            return float(value)
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _parse_input_date(value: Optional[str]) -> Optional[date]:
        if not value:
            return None
        for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None
