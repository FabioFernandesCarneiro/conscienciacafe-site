#!/usr/bin/env python3
"""
Database Manager - Sistema de Armazenamento Local
Gerencia a estrutura SQLite local para substituir dependência do Omie
"""

import os
import sqlite3
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import json

DEFAULT_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'local_financeiro.db'))

class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        # Resolver caminho do banco
        if db_path is None:
            db_path = DEFAULT_DB_PATH
        self.db_path = os.path.abspath(db_path)
        self.ensure_data_directory()
        self.init_database()

    def ensure_data_directory(self):
        """Garante que o diretório data existe"""
        dir_path = os.path.dirname(self.db_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

    def get_connection(self):
        """Retorna conexão com o banco"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Para acessar por nome da coluna
        return conn

    def init_database(self):
        """Inicializa todas as tabelas do banco de dados"""
        conn = self.get_connection()
        try:
            # 1. TABELA DE CONTAS
            conn.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY,
                    omie_id INTEGER UNIQUE,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL, -- 'checking', 'credit', 'cash'
                    bank_name TEXT,
                    account_number TEXT,
                    balance DECIMAL(15,2) DEFAULT 0,
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 2. TABELA DE CATEGORIAS
            conn.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY,
                    omie_code TEXT UNIQUE,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL, -- 'R' (receita), 'D' (despesa), 'N' (neutro)
                    parent_category_id INTEGER,
                    ml_keywords TEXT, -- JSON array de palavras-chave para ML
                    color TEXT DEFAULT '#6c757d',
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_category_id) REFERENCES categories(id)
                )
            ''')

            # 3. TABELA DE CLIENTES/FORNECEDORES
            conn.execute('''
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY,
                    omie_id INTEGER UNIQUE,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL, -- 'Cliente', 'Fornecedor'
                    email TEXT,
                    phone TEXT,
                    document TEXT, -- CPF/CNPJ
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 4. TABELA PRINCIPAL DE TRANSAÇÕES
            conn.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY,
                    account_id INTEGER NOT NULL,
                    omie_code TEXT, -- Código original do Omie (para reconciliação)
                    date DATE NOT NULL,
                    description TEXT NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    type TEXT NOT NULL, -- 'credit', 'debit'
                    balance DECIMAL(15,2), -- Saldo após transação
                    category_id INTEGER,
                    client_id INTEGER,
                    document_number TEXT,
                    source_file TEXT, -- Arquivo de origem (OFX, CSV, etc)
                    import_batch_id INTEGER,
                    reconciled_status TEXT DEFAULT 'pending', -- 'pending', 'reconciled', 'manual'
                    reconciled_at TIMESTAMP,
                    ml_confidence DECIMAL(3,2), -- 0.00 a 1.00
                    ml_suggestions TEXT, -- JSON com sugestões do ML
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts(id),
                    FOREIGN KEY (category_id) REFERENCES categories(id),
                    FOREIGN KEY (client_id) REFERENCES clients(id),
                    FOREIGN KEY (import_batch_id) REFERENCES import_batches(id)
                )
            ''')

            # 5. TABELA DE LOTES DE IMPORTAÇÃO
            conn.execute('''
                CREATE TABLE IF NOT EXISTS import_batches (
                    id INTEGER PRIMARY KEY,
                    source TEXT NOT NULL, -- 'omie_migration', 'ofx_import', 'csv_import'
                    source_file TEXT,
                    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_records INTEGER DEFAULT 0,
                    successful_records INTEGER DEFAULT 0,
                    failed_records INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'processing', -- 'processing', 'completed', 'failed'
                    error_log TEXT,
                    metadata TEXT -- JSON com informações adicionais
                )
            ''')

            # 6. TABELA DE DADOS DE TREINAMENTO ML
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ml_training_data (
                    id INTEGER PRIMARY KEY,
                    transaction_id INTEGER,
                    original_description TEXT NOT NULL,
                    normalized_description TEXT,
                    predicted_category_id INTEGER,
                    actual_category_id INTEGER,
                    predicted_client_id INTEGER,
                    actual_client_id INTEGER,
                    confidence DECIMAL(3,2),
                    user_corrected BOOLEAN DEFAULT 0,
                    training_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (transaction_id) REFERENCES transactions(id),
                    FOREIGN KEY (predicted_category_id) REFERENCES categories(id),
                    FOREIGN KEY (actual_category_id) REFERENCES categories(id),
                    FOREIGN KEY (predicted_client_id) REFERENCES clients(id),
                    FOREIGN KEY (actual_client_id) REFERENCES clients(id)
                )
            ''')

            # 7. CRM - LEADS
            conn.execute('''
                CREATE TABLE IF NOT EXISTS crm_leads (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT,
                    status TEXT DEFAULT 'new',
                    source TEXT,
                    search_keyword TEXT,
                    search_city TEXT,
                    address_line TEXT,
                    address_number TEXT,
                    address_complement TEXT,
                    neighborhood TEXT,
                    city TEXT,
                    state TEXT,
                    postal_code TEXT,
                    country TEXT,
                    latitude REAL,
                    longitude REAL,
                    phone TEXT,
                    whatsapp TEXT,
                    email TEXT,
                    instagram TEXT,
                    website TEXT,
                    primary_contact_name TEXT,
                    owner TEXT,
                    notes TEXT,
                    google_place_id TEXT,
                    is_customer BOOLEAN DEFAULT 0,
                    converted_account_id INTEGER,
                    last_stage_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (converted_account_id) REFERENCES clients(id)
                )
            ''')

            # 8. CRM - INTERAÇÕES
            conn.execute('''
                CREATE TABLE IF NOT EXISTS crm_interactions (
                    id INTEGER PRIMARY KEY,
                    lead_id INTEGER NOT NULL,
                    interaction_type TEXT,
                    channel TEXT,
                    subject TEXT,
                    notes TEXT,
                    interaction_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    follow_up_at TIMESTAMP,
                    owner TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lead_id) REFERENCES crm_leads(id) ON DELETE CASCADE
                )
            ''')

            # ÍNDICES PARA PERFORMANCE
            conn.execute('CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_transactions_reconciled ON transactions(reconciled_status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_transactions_omie_code ON transactions(omie_code)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_crm_leads_status ON crm_leads(status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_crm_leads_city ON crm_leads(city)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_crm_leads_owner ON crm_leads(owner)')
            conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_crm_leads_google_place ON crm_leads(google_place_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_crm_interactions_lead ON crm_interactions(lead_id)')

            conn.commit()
            print("✅ Database schema criado com sucesso!")

        except Exception as e:
            print(f"❌ Erro ao criar schema: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def insert_account(self, omie_id: int, name: str, account_type: str, bank_name: str = None) -> int:
        """Insere uma nova conta"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                INSERT OR REPLACE INTO accounts (omie_id, name, type, bank_name)
                VALUES (?, ?, ?, ?)
            ''', (omie_id, name, account_type, bank_name))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def insert_category(self, omie_code: str, name: str, category_type: str, keywords: List[str] = None) -> int:
        """Insere uma nova categoria"""
        conn = self.get_connection()
        try:
            keywords_json = json.dumps(keywords) if keywords else None
            cursor = conn.execute('''
                INSERT OR REPLACE INTO categories (omie_code, name, type, ml_keywords)
                VALUES (?, ?, ?, ?)
            ''', (omie_code, name, category_type, keywords_json))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def insert_client(self, omie_id: int, name: str, client_type: str, email: str = None, phone: str = None) -> int:
        """Insere um novo cliente/fornecedor"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                INSERT OR REPLACE INTO clients (omie_id, name, type, email, phone)
                VALUES (?, ?, ?, ?, ?)
            ''', (omie_id, name, client_type, email, phone))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def insert_transaction(self, account_id: int, date: date, description: str, amount: float,
                          transaction_type: str, balance: float = None, category_id: int = None,
                          client_id: int = None, omie_code: str = None, import_batch_id: int = None,
                          document_number: str = None) -> int:
        """Insere uma nova transação"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                INSERT INTO transactions
                (account_id, date, description, amount, type, balance, category_id, client_id, omie_code, import_batch_id, document_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (account_id, date, description, amount, transaction_type, balance, category_id, client_id, omie_code, import_batch_id, document_number))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def create_import_batch(self, source: str, source_file: str = None, metadata: dict = None) -> int:
        """Cria um novo lote de importação"""
        conn = self.get_connection()
        try:
            metadata_json = json.dumps(metadata) if metadata else None
            cursor = conn.execute('''
                INSERT INTO import_batches (source, source_file, metadata)
                VALUES (?, ?, ?)
            ''', (source, source_file, metadata_json))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def update_import_batch(self, batch_id: int, total_records: int = None, successful_records: int = None,
                           failed_records: int = None, status: str = None, error_log: str = None):
        """Atualiza status de um lote de importação"""
        conn = self.get_connection()
        try:
            updates = []
            params = []

            if total_records is not None:
                updates.append("total_records = ?")
                params.append(total_records)
            if successful_records is not None:
                updates.append("successful_records = ?")
                params.append(successful_records)
            if failed_records is not None:
                updates.append("failed_records = ?")
                params.append(failed_records)
            if status:
                updates.append("status = ?")
                params.append(status)
            if error_log:
                updates.append("error_log = ?")
                params.append(error_log)

            if updates:
                params.append(batch_id)
                query = f"UPDATE import_batches SET {', '.join(updates)} WHERE id = ?"
                conn.execute(query, params)
                conn.commit()
        finally:
            conn.close()

    def get_account_by_omie_id(self, omie_id: int) -> Optional[Dict]:
        """Busca conta pelo ID do Omie"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('SELECT * FROM accounts WHERE omie_id = ?', (omie_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_category_by_omie_code(self, omie_code: str) -> Optional[Dict]:
        """Busca categoria pelo código do Omie"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('SELECT * FROM categories WHERE omie_code = ?', (omie_code,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_client_by_omie_id(self, omie_id: int) -> Optional[Dict]:
        """Busca cliente pelo ID do Omie"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('SELECT * FROM clients WHERE omie_id = ?', (omie_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_transactions(self, account_id: int = None, start_date: date = None, end_date: date = None,
                        limit: int = 1000) -> List[Dict]:
        """Busca transações com filtros"""
        conn = self.get_connection()
        try:
            query = '''
                SELECT t.*, a.name as account_name, c.name as category_name, cl.name as client_name
                FROM transactions t
                LEFT JOIN accounts a ON t.account_id = a.id
                LEFT JOIN categories c ON t.category_id = c.id
                LEFT JOIN clients cl ON t.client_id = cl.id
                WHERE 1=1
            '''
            params = []

            if account_id:
                query += ' AND t.account_id = ?'
                params.append(account_id)
            if start_date:
                query += ' AND t.date >= ?'
                params.append(start_date)
            if end_date:
                query += ' AND t.date <= ?'
                params.append(end_date)

            query += ' ORDER BY t.date DESC, t.id DESC LIMIT ?'
            params.append(limit)

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    # ==========================
    # CRM - LEADS E INTERAÇÕES
    # ==========================

    def create_crm_lead(self, lead_data: Dict[str, Any]) -> int:
        """Cria um novo lead no módulo CRM"""
        if not lead_data.get('name'):
            raise ValueError('Campo name é obrigatório para criar um lead')

        allowed_fields = [
            'name', 'category', 'status', 'source', 'search_keyword', 'search_city',
            'address_line', 'address_number', 'address_complement', 'neighborhood',
            'city', 'state', 'postal_code', 'country', 'latitude', 'longitude',
            'phone', 'whatsapp', 'email', 'instagram', 'website', 'primary_contact_name',
            'owner', 'notes', 'google_place_id', 'is_customer', 'converted_account_id'
        ]

        payload = {key: lead_data.get(key) for key in allowed_fields if lead_data.get(key) is not None}
        if 'is_customer' in payload:
            payload['is_customer'] = int(bool(payload['is_customer']))

        fields = list(payload.keys())
        placeholders = ', '.join(['?'] * len(fields))
        query = f"INSERT INTO crm_leads ({', '.join(fields)}) VALUES ({placeholders})"

        conn = self.get_connection()
        try:
            cursor = conn.execute(query, [payload[field] for field in fields])
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def update_crm_lead(self, lead_id: int, updates: Dict[str, Any]) -> None:
        """Atualiza campos de um lead existente"""
        if not updates:
            return

        allowed_fields = [
            'name', 'category', 'status', 'source', 'search_keyword', 'search_city',
            'address_line', 'address_number', 'address_complement', 'neighborhood',
            'city', 'state', 'postal_code', 'country', 'latitude', 'longitude',
            'phone', 'whatsapp', 'email', 'instagram', 'website', 'primary_contact_name',
            'owner', 'notes', 'google_place_id', 'is_customer', 'converted_account_id'
        ]

        set_clauses = []
        values = []
        status_changed = False

        for field in allowed_fields:
            if field in updates and updates[field] is not None:
                value = updates[field]
                if field == 'is_customer':
                    value = int(bool(value))
                set_clauses.append(f"{field} = ?")
                values.append(value)
                if field == 'status':
                    status_changed = True

        if not set_clauses:
            return

        set_clauses.append('updated_at = CURRENT_TIMESTAMP')
        if status_changed:
            set_clauses.append('last_stage_change = CURRENT_TIMESTAMP')

        values.append(lead_id)
        query = f"UPDATE crm_leads SET {', '.join(set_clauses)} WHERE id = ?"

        conn = self.get_connection()
        try:
            conn.execute(query, values)
            conn.commit()
        finally:
            conn.close()

    def get_crm_lead(self, lead_id: int) -> Optional[Dict[str, Any]]:
        """Obtém dados completos de um lead"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('SELECT * FROM crm_leads WHERE id = ?', (lead_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_crm_leads(self, status: Optional[str] = None, owner: Optional[str] = None,
                       city: Optional[str] = None, is_customer: Optional[bool] = None,
                       search: Optional[str] = None, limit: int = 200, offset: int = 0) -> List[Dict[str, Any]]:
        """Lista leads com filtros opcionais"""
        query = 'SELECT * FROM crm_leads WHERE 1=1'
        params: List[Any] = []

        if status:
            query += ' AND status = ?'
            params.append(status)
        if owner:
            query += ' AND owner = ?'
            params.append(owner)
        if city:
            query += ' AND city = ?'
            params.append(city)
        if is_customer is not None:
            query += ' AND is_customer = ?'
            params.append(int(bool(is_customer)))
        if search:
            pattern = f"%{search.lower()}%"
            query += ' AND (LOWER(name) LIKE ? OR LOWER(city) LIKE ? OR LOWER(state) LIKE ?)'
            params.extend([pattern, pattern, pattern])

        query += ' ORDER BY updated_at DESC, id DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        conn = self.get_connection()
        try:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def delete_crm_lead(self, lead_id: int) -> None:
        """Remove um lead do CRM"""
        conn = self.get_connection()
        try:
            conn.execute('DELETE FROM crm_leads WHERE id = ?', (lead_id,))
            conn.commit()
        finally:
            conn.close()

    def add_crm_interaction(self, lead_id: int, interaction: Dict[str, Any]) -> int:
        """Adiciona interação relacionada a um lead"""
        allowed_fields = [
            'interaction_type', 'channel', 'subject', 'notes',
            'interaction_at', 'follow_up_at', 'owner', 'metadata'
        ]

        payload = {key: interaction.get(key) for key in allowed_fields if interaction.get(key) is not None}
        payload['lead_id'] = lead_id

        fields = list(payload.keys())
        placeholders = ', '.join(['?'] * len(fields))
        query = f"INSERT INTO crm_interactions ({', '.join(fields)}) VALUES ({placeholders})"

        conn = self.get_connection()
        try:
            cursor = conn.execute(query, [payload[field] for field in fields])
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def list_crm_interactions(self, lead_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Lista interações de um lead"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                '''
                SELECT * FROM crm_interactions
                WHERE lead_id = ?
                ORDER BY interaction_at DESC, id DESC
                LIMIT ?
                ''',
                (lead_id, limit)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_statistics(self) -> Dict:
        """Retorna estatísticas do banco"""
        conn = self.get_connection()
        try:
            stats = {}

            # Contadores gerais
            cursor = conn.execute('SELECT COUNT(*) FROM accounts WHERE active = 1')
            stats['total_accounts'] = cursor.fetchone()[0]

            cursor = conn.execute('SELECT COUNT(*) FROM categories WHERE active = 1')
            stats['total_categories'] = cursor.fetchone()[0]

            cursor = conn.execute('SELECT COUNT(*) FROM clients WHERE active = 1')
            stats['total_clients'] = cursor.fetchone()[0]

            cursor = conn.execute('SELECT COUNT(*) FROM transactions')
            stats['total_transactions'] = cursor.fetchone()[0]

            # Período dos dados
            cursor = conn.execute('SELECT MIN(date), MAX(date) FROM transactions')
            date_range = cursor.fetchone()
            stats['date_range'] = {
                'start': date_range[0],
                'end': date_range[1]
            }

            # Status de conciliação
            cursor = conn.execute('''
                SELECT reconciled_status, COUNT(*)
                FROM transactions
                GROUP BY reconciled_status
            ''')
            stats['reconciliation_status'] = dict(cursor.fetchall())

            return stats
        finally:
            conn.close()
