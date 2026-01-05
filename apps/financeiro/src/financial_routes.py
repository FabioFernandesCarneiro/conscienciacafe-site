from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
import os
from werkzeug.utils import secure_filename

from .services.transaction_service import TransactionService
from .models import Account, Category, Transaction
from .db import session_scope

def create_financial_blueprint():
    bp = Blueprint('financial', __name__, url_prefix='/financial')
    service = TransactionService()
    
    @bp.route('/import', methods=['GET', 'POST'])
    def import_data():
        if request.method == 'POST':
            # Handle OFX Upload
            if 'ofx_file' in request.files:
                file = request.files['ofx_file']
                account_id = request.form.get('account_id')
                
                if file and file.filename and account_id:
                    filename = secure_filename(file.filename)
                    filepath = os.path.join('/tmp', filename)
                    file.save(filepath)
                    
                    try:
                        stats = service.import_ofx(filepath, int(account_id))
                        flash(f"Importado com sucesso: {stats['imported']} transações. {stats['skipped']} duplicadas.", 'success')
                    except Exception as e:
                        flash(f"Erro ao importar OFX: {e}", 'error')
                    finally:
                        if os.path.exists(filepath):
                            os.remove(filepath)
                            
            # Handle Sheet Sync
            elif 'sheet_url' in request.form:
                sheet_url = request.form.get('sheet_url')
                account_id = request.form.get('sheet_account_id')
                
                if sheet_url and account_id:
                    try:
                        stats = service.import_from_sheet(sheet_url, int(account_id))
                        flash(f"Sincronizado com sucesso: {stats['imported']} transações. {stats['skipped']} duplicadas.", 'success')
                    except Exception as e:
                        flash(f"Erro ao sincronizar planilha: {e}", 'error')
                        
            return redirect(url_for('financial.review'))
            
        # GET: Show Import Form
        with session_scope() as session:
            accounts = session.query(Account).filter(Account.active == True).all()
            return render_template('financial/import.html', accounts=accounts)

    @bp.route('/review')
    def review():
        with session_scope() as session:
            # Pending transactions (not reconciled)
            # For now, let's just show all recent transactions or filter by status if we add one
            # The user wants to categorize and identify transfers
            
            # Get recent transactions
            transactions = session.query(Transaction).order_by(Transaction.date.desc()).limit(100).all()
            categories = session.query(Category).filter(Category.active == True).order_by(Category.name).all()
            accounts = session.query(Account).all()
            
            # Detect potential transfers
            suggested_transfers = service.detect_transfers()
            
            return render_template('financial/review.html', 
                                 transactions=transactions, 
                                 categories=categories,
                                 accounts=accounts,
                                 suggested_transfers=suggested_transfers)

    @bp.route('/api/transaction/<int:t_id>', methods=['POST'])
    def update_transaction(t_id):
        data = request.json
        updated = service.update_transaction(t_id, data)
        if updated:
            return jsonify({'success': True})
        return jsonify({'success': False}), 400

    @bp.route('/api/confirm-transfer', methods=['POST'])
    def confirm_transfer():
        data = request.json
        service.confirm_transfer(data['outbound_id'], data['inbound_id'])
        return jsonify({'success': True})

    @bp.route('/dre')
    def dre():
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        
        result = service.get_monthly_result(year, month)
        
        return render_template('financial/dre.html', 
                             result=result, 
                             year=year, 
                             month=month)
                             
    return bp
