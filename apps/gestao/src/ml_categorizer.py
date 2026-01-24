"""
Sistema de categorização inteligente usando Machine Learning
"""

import pickle
import sqlite3
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from typing import Dict, List, Tuple, Optional
import os

class MLCategorizer:
    def __init__(self, db_path: str = "./data/learning_data.db"):
        self.db_path = db_path
        self.model = None
        self.categories_mapping = {}
        self.clients_mapping = {}
        self.model_path = "./models/categorizer_model.pkl"
        
        # Criar diretórios se não existirem
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        self._init_database()
        self._load_model()
    
    def _init_database(self):
        """Inicializa banco de dados para armazenar dados de aprendizado"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                clean_description TEXT NOT NULL,
                amount REAL NOT NULL,
                category_id TEXT,
                category_name TEXT,
                client_supplier_id TEXT,
                client_supplier_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_model(self):
        """Carrega modelo treinado se existir"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.model = model_data['model']
                    self.categories_mapping = model_data['categories_mapping']
                    self.clients_mapping = model_data['clients_mapping']
                print("Modelo carregado com sucesso!")
            except Exception as e:
                print(f"Erro ao carregar modelo: {e}")
                self.model = None
    
    def _save_model(self):
        """Salva modelo treinado"""
        try:
            model_data = {
                'model': self.model,
                'categories_mapping': self.categories_mapping,
                'clients_mapping': self.clients_mapping
            }
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            print("Modelo salvo com sucesso!")
        except Exception as e:
            print(f"Erro ao salvar modelo: {e}")
    
    def add_learning_data(self, description: str, clean_description: str, amount: float,
                         category_id: str = None, category_name: str = None,
                         client_supplier_id: str = None, client_supplier_name: str = None):
        """Adiciona dados para aprendizado do modelo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO learning_data 
            (description, clean_description, amount, category_id, category_name, 
             client_supplier_id, client_supplier_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (description, clean_description, amount, category_id, category_name,
              client_supplier_id, client_supplier_name))
        
        conn.commit()
        conn.close()
        
        # Retreinar modelo com novos dados
        self.train_model()
    
    def train_model(self):
        """Treina modelo com dados disponíveis"""
        conn = sqlite3.connect(self.db_path)
        
        # Carregar dados
        df = pd.read_sql_query('''
            SELECT description, clean_description, amount, category_name, client_supplier_name
            FROM learning_data
            WHERE category_name IS NOT NULL
        ''', conn)
        
        conn.close()
        
        if len(df) < 5:  # Mínimo de exemplos para treinar
            print("Dados insuficientes para treinar modelo (mínimo 5 exemplos)")
            return
        
        try:
            # Preparar features
            features = df['clean_description'] + ' ' + df['amount'].astype(str)
            
            # Preparar targets para categorias
            categories = df['category_name'].fillna('outros')
            
            # Criar pipeline para categorização
            self.model = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=1000, stop_words=None, ngram_range=(1, 2))),
                ('classifier', MultinomialNB())
            ])
            
            # Treinar modelo
            self.model.fit(features, categories)
            
            # Criar mapeamentos
            self.categories_mapping = {cat: i for i, cat in enumerate(categories.unique())}
            
            # Treinar para clientes/fornecedores se houver dados
            clients_df = df[df['client_supplier_name'].notna()]
            if len(clients_df) > 0:
                self.clients_mapping = {client: i for i, client in enumerate(clients_df['client_supplier_name'].unique())}
            
            self._save_model()
            print(f"Modelo treinado com {len(df)} exemplos!")
            
        except Exception as e:
            print(f"Erro ao treinar modelo: {e}")
    
    def predict_category(self, description: str, clean_description: str, amount: float) -> Tuple[Optional[str], float]:
        """Prediz categoria da transação"""
        if self.model is None:
            return None, 0.0
        
        try:
            feature = clean_description + ' ' + str(amount)
            prediction = self.model.predict([feature])[0]
            
            # Calcular confiança
            probabilities = self.model.predict_proba([feature])[0]
            confidence = max(probabilities)
            
            return prediction, confidence
            
        except Exception as e:
            print(f"Erro na predição: {e}")
            return None, 0.0
    
    def suggest_similar_transactions(self, clean_description: str, limit: int = 5) -> List[Dict]:
        """Sugere transações similares do histórico"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Busca por similaridade básica (pode ser melhorada com fuzzy matching)
        words = clean_description.split()
        
        suggestions = []
        for word in words:
            cursor.execute('''
                SELECT DISTINCT description, category_name, client_supplier_name, 
                       COUNT(*) as frequency
                FROM learning_data 
                WHERE clean_description LIKE ? 
                AND (category_name IS NOT NULL OR client_supplier_name IS NOT NULL)
                GROUP BY description, category_name, client_supplier_name
                ORDER BY frequency DESC
                LIMIT ?
            ''', (f'%{word}%', limit))
            
            results = cursor.fetchall()
            for result in results:
                suggestions.append({
                    'description': result[0],
                    'category': result[1],
                    'client_supplier': result[2],
                    'frequency': result[3]
                })
        
        conn.close()
        
        # Remover duplicatas e ordenar por frequência
        unique_suggestions = []
        seen = set()
        for suggestion in suggestions:
            key = (suggestion['description'], suggestion['category'], suggestion['client_supplier'])
            if key not in seen:
                unique_suggestions.append(suggestion)
                seen.add(key)
        
        return sorted(unique_suggestions, key=lambda x: x['frequency'], reverse=True)[:limit]
    
    def get_learning_stats(self) -> Dict[str, int]:
        """Retorna estatísticas dos dados de aprendizado"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM learning_data')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM learning_data WHERE category_name IS NOT NULL')
        with_category = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM learning_data WHERE client_supplier_name IS NOT NULL')
        with_client = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_transactions': total,
            'categorized': with_category,
            'with_client_supplier': with_client,
            'model_trained': self.model is not None
        }


# ==========================
# Helper Functions
# ==========================

def clean_description_for_ml(description: str) -> str:
    """Clean description for ML processing."""
    import re

    if not description:
        return ""

    clean = description.lower()
    clean = re.sub(r'[^\w\s]', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()

    return clean


def extract_name_from_description(description: str) -> Optional[str]:
    """Extract person/company name from transaction description."""
    import re

    if not description:
        return None

    patterns = [
        r'pix.*?-\s*([A-Z][A-Z\s]+[A-Z])',
        r'transferência.*?-\s*([A-Z][A-Z\s]+[A-Z])',
        r'para\s+([A-Z][A-Z\s]+[A-Z])',
        r'de\s+([A-Z][A-Z\s]+[A-Z])',
    ]

    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name.split()) >= 2 and len(name) > 5:
                return name.title()

    return None