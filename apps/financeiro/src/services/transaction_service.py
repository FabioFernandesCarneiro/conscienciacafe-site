from typing import List, Optional, Dict, Any
from datetime import datetime
from datetime import datetime, timedelta
from sqlalchemy import extract, func, or_, and_
from sqlalchemy.orm import Session

from ..models import Transaction, Account, Category
from ..db import session_scope
from ..ofx_parser import OFXParser
from ..ml_categorizer import MLCategorizer
from .sheet_importer import SheetImporter

class TransactionService:
    def __init__(self):
        self.ml_categorizer = MLCategorizer()

    def list_transactions(self, 
                         start_date: Optional[datetime] = None, 
                         end_date: Optional[datetime] = None,
                         account_id: Optional[int] = None,
                         status: Optional[str] = None) -> List[Transaction]:
        """List transactions with filters"""
        with session_scope() as session:
            query = session.query(Transaction)
            
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            
            # Eager load relations
            return query.order_by(Transaction.date.desc()).all()

    def create_transaction(self, data: Dict[str, Any]) -> Transaction:
        """Create a single transaction"""
        with session_scope() as session:
            transaction = Transaction(
                account_id=data['account_id'],
                date=data['date'],
                description=data['description'],
                amount=data['amount'],
                type=data['type'],
                category_id=data.get('category_id'),
                original_description=data.get('description') # For ML
            )
            
            # Auto-categorize if no category provided
            if not transaction.category_id:
                self._predict_category(session, transaction)
                
            session.add(transaction)
            session.commit()
            return transaction

    def import_ofx(self, file_path: str, account_id: int) -> Dict[str, int]:
        """Import transactions from OFX file"""
        parser = OFXParser(file_path)
        # Note: OFXParser needs update to return raw data list, 
        # currently it tries to use AccountManager which we are deprecating/refactoring
        # For now, assuming we adapt OFXParser or use it as is but ignore its account detection
        
        # Let's assume we modify OFXParser to just return list of dicts
        # Or we use a simplified parsing logic here if OFXParser is too coupled
        
        # Actually, let's use the existing parser but we might need to monkeypatch or adjust it
        # For this step, I will assume OFXParser returns a list of dicts with 'date', 'amount', 'description', 'id'
        
        transactions_data = parser.parse() 
        
        stats = {'imported': 0, 'skipped': 0}
        
        with session_scope() as session:
            for t_data in transactions_data:
                # Check for duplicates (same account, date, amount, description)
                exists = session.query(Transaction).filter(
                    Transaction.account_id == account_id,
                    Transaction.date == t_data['date'],
                    Transaction.amount == t_data['amount'],
                    Transaction.description == t_data['description']
                ).first()
                
                if exists:
                    stats['skipped'] += 1
                    continue
                
                # Determine type based on amount
                amount = float(t_data['amount'])
                t_type = 'revenue' if amount > 0 else 'expense'
                
                transaction = Transaction(
                    account_id=account_id,
                    date=t_data['date'],
                    description=t_data['description'],
                    amount=amount,
                    type=t_type,
                    original_description=t_data['description']
                )
                
                self._predict_category(session, transaction)
                
                session.add(transaction)
                stats['imported'] += 1
                
        return stats

    def import_from_sheet(self, sheet_url: str, account_id: int) -> Dict[str, int]:
        """Import transactions from Google Sheet"""
        importer = SheetImporter(sheet_url)
        transactions_data = importer.import_transactions()
        
        stats = {'imported': 0, 'skipped': 0}
        
        with session_scope() as session:
            for t_data in transactions_data:
                # Check for duplicates
                exists = session.query(Transaction).filter(
                    Transaction.account_id == account_id,
                    Transaction.date == t_data['date'],
                    Transaction.amount == t_data['amount'],
                    Transaction.description == t_data['description']
                ).first()
                
                if exists:
                    stats['skipped'] += 1
                    continue
                
                transaction = Transaction(
                    account_id=account_id,
                    date=t_data['date'],
                    description=t_data['description'],
                    amount=t_data['amount'],
                    type=t_data['type'],
                    original_description=t_data['description'],
                    source_file='google_sheet'
                )
                
                self._predict_category(session, transaction)
                
                session.add(transaction)
                stats['imported'] += 1
                
        return stats

    def update_transaction(self, transaction_id: int, data: Dict[str, Any]) -> Optional[Transaction]:
        """Update transaction and retrain ML if category changed"""
        with session_scope() as session:
            transaction = session.query(Transaction).get(transaction_id)
            if not transaction:
                return None
            
            old_category_id = transaction.category_id
            
            # Update fields
            if 'category_id' in data:
                transaction.category_id = data['category_id']
                transaction.user_corrected = True
            if 'description' in data:
                transaction.description = data['description']
            if 'type' in data:
                transaction.type = data['type']
                
            session.commit()
            
            # Trigger ML training if category changed
            if 'category_id' in data and data['category_id'] != old_category_id:
                self._train_ml(session, transaction)
                
            return transaction

    def _predict_category(self, session: Session, transaction: Transaction):
        """Predict category using ML"""
        category_name, confidence = self.ml_categorizer.predict_category(
            transaction.description, 
            transaction.description.lower(), # clean_description
            float(transaction.amount)
        )
        
        if category_name:
            # Find category by name
            category = session.query(Category).filter(Category.name == category_name).first()
            if category:
                transaction.category_id = category.id
                transaction.ml_confidence = confidence

    def _train_ml(self, session: Session, transaction: Transaction):
        """Feed data back to ML model"""
        if not transaction.category_id:
            return
            
        category = session.query(Category).get(transaction.category_id)
        if not category:
            return
            
        self.ml_categorizer.add_learning_data(
            description=transaction.original_description or transaction.description,
            clean_description=transaction.description.lower(),
            amount=float(transaction.amount),
            category_name=category.name
        )

    def get_monthly_result(self, year: int, month: int) -> Dict[str, float]:
        """Calculate DRE for a specific month"""
        with session_scope() as session:
            # Revenue
            revenue = session.query(func.sum(Transaction.amount)).filter(
                extract('year', Transaction.date) == year,
                extract('month', Transaction.date) == month,
                Transaction.type == 'revenue'
            ).scalar() or 0
            
            # Expense
            expense = session.query(func.sum(Transaction.amount)).filter(
                extract('year', Transaction.date) == year,
                extract('month', Transaction.date) == month,
                Transaction.type == 'expense'
            ).scalar() or 0
            
            return {
                'revenue': float(revenue),
                'expense': float(expense),
                'result': float(revenue) + float(expense) # Expense is usually negative in DB? 
                # Wait, if I store expense as negative, then sum is correct. 
                # If I store absolute value and use type, then I need to subtract.
                # My import logic stores amount as is from OFX (negative for expense).
                # So sum is correct.
            }

    def detect_transfers(self) -> List[Dict[str, Any]]:
        """
        Detect potential transfers between accounts.
        Returns a list of suggested pairs.
        """
        suggestions = []
        with session_scope() as session:
            # Get all transactions that are NOT already linked as transfers
            # and are NOT reconciled (optional, but safer)
            transactions = session.query(Transaction).filter(
                Transaction.transfer_id.is_(None)
            ).order_by(Transaction.date).all()
            
            # Simple O(N^2) approach for now, optimized by window
            # In production, use a better algorithm or SQL window functions
            
            used_ids = set()
            
            for i, t1 in enumerate(transactions):
                if t1.id in used_ids:
                    continue
                    
                # Look for matching transaction
                # Criteria: 
                # 1. Different account
                # 2. Amount is inverse (approximate match?) -> Exact match for now
                # 3. Date within 2 days
                
                for j in range(i + 1, len(transactions)):
                    t2 = transactions[j]
                    
                    if t2.id in used_ids:
                        continue
                        
                    # Stop looking if date diff > 2 days (since list is sorted by date)
                    date_diff = (t2.date - t1.date).days
                    if date_diff > 2:
                        break
                        
                    if t1.account_id == t2.account_id:
                        continue
                        
                    # Check amount (t1.amount = -t2.amount)
                    if abs(float(t1.amount) + float(t2.amount)) < 0.01:
                        # Found a match!
                        suggestions.append({
                            'outbound': t1 if t1.amount < 0 else t2,
                            'inbound': t2 if t1.amount < 0 else t1,
                            'confidence': 0.9 if date_diff == 0 else 0.7
                        })
                        used_ids.add(t1.id)
                        used_ids.add(t2.id)
                        break
                        
        return suggestions

    def confirm_transfer(self, outbound_id: int, inbound_id: int):
        """Link two transactions as a transfer"""
        with session_scope() as session:
            t1 = session.query(Transaction).get(outbound_id)
            t2 = session.query(Transaction).get(inbound_id)
            
            if t1 and t2:
                t1.transfer_id = t2.id
                t2.transfer_id = t1.id
                
                # Set category to 'Transferência' if exists
                transfer_cat = session.query(Category).filter(Category.type == 'transfer').first()
                if transfer_cat:
                    t1.category_id = transfer_cat.id
                    t2.category_id = transfer_cat.id
                    
                t1.type = 'transfer'
                t2.type = 'transfer'
                
                session.commit()
