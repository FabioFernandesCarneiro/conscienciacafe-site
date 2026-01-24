"""Blueprint de autenticação para o sistema."""

from __future__ import annotations

from typing import Optional
from urllib.parse import urlparse, urljoin

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

from .auth_service import AuthService


def _is_safe_url(target: Optional[str]) -> bool:
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def create_auth_blueprint(auth_service: AuthService) -> Blueprint:
    bp = Blueprint('auth', __name__, url_prefix='/auth')

    @bp.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            next_url = request.args.get('next')
            if next_url and _is_safe_url(next_url):
                return redirect(next_url)
            return redirect(url_for('dashboard'))

        error = None
        next_url = request.args.get('next')

        if request.method == 'POST':
            username = (request.form.get('username') or '').strip()
            password = request.form.get('password') or ''

            user = auth_service.authenticate(username, password)
            if user:
                login_user(user, remember=True)
                flash('Login realizado com sucesso!', 'success')
                redirect_target = request.form.get('next') or next_url
                if redirect_target and _is_safe_url(redirect_target):
                    return redirect(redirect_target)
                return redirect(url_for('dashboard'))

            error = 'Usuário ou senha inválidos.'
            flash(error, 'danger')

        return render_template('auth/login.html', next=next_url or request.referrer)

    @bp.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Sessão encerrada.', 'info')
        return redirect(url_for('auth.login'))

    @bp.route('/change-password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        if request.method == 'POST':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            if new_password != confirm_password:
                flash('A nova senha e a confirmação não conferem.', 'danger')
                return render_template('auth/change_password.html')

            user_record = auth_service.db.get_crm_user_by_id(int(current_user.get_id()))
            if not user_record or not user_record.get('password_hash') or not check_password_hash(user_record['password_hash'], current_password):
                flash('Senha atual incorreta.', 'danger')
                return render_template('auth/change_password.html')

            try:
                auth_service.update_password(int(current_user.get_id()), new_password)
            except ValueError as exc:
                flash(str(exc), 'danger')
                return render_template('auth/change_password.html')

            flash('Senha alterada com sucesso!', 'success')
            return redirect(url_for('dashboard'))

        return render_template('auth/change_password.html')

    def _require_admin():
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Acesso negado.', 'danger')
            return False
        return True

    @bp.route('/users', methods=['GET'])
    @login_required
    def list_users():
        if not _require_admin():
            return redirect(url_for('dashboard'))

        users = auth_service.list_users()
        return render_template('auth/users.html', users=users)

    @bp.route('/users/new', methods=['GET', 'POST'])
    @login_required
    def new_user():
        if not _require_admin():
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            username = (request.form.get('username') or '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            role = (request.form.get('role') or 'user').strip().lower()
            country = (request.form.get('country') or '').strip().upper() or None

            if password != confirm_password:
                flash('A senha e a confirmação não conferem.', 'danger')
                return render_template('auth/new_user.html')

            try:
                auth_service.create_user(username, password, role, country)
            except ValueError as exc:
                flash(str(exc), 'danger')
                return render_template('auth/new_user.html')

            flash(f'Usuário {username} criado com sucesso!', 'success')
            return redirect(url_for('auth.list_users'))

        return render_template('auth/new_user.html')

    @bp.route('/users/<int:user_id>/toggle', methods=['POST'])
    @login_required
    def toggle_user(user_id):
        if not _require_admin():
            return redirect(url_for('dashboard'))

        # Não permitir desativar o próprio usuário
        if user_id == int(current_user.get_id()):
            flash('Você não pode desativar seu próprio usuário.', 'danger')
            return redirect(url_for('auth.list_users'))

        user = auth_service.load_user_by_id(user_id)
        if user:
            new_status = not user.raw.get('active')
            auth_service.set_user_active(user_id, new_status)
            status_text = 'ativado' if new_status else 'desativado'
            flash(f'Usuário {status_text} com sucesso!', 'success')
        else:
            flash('Usuário não encontrado.', 'danger')

        return redirect(url_for('auth.list_users'))

    @bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_user(user_id):
        if not _require_admin():
            return redirect(url_for('dashboard'))

        user = auth_service.load_user_by_id(user_id)
        if not user:
            flash('Usuário não encontrado.', 'danger')
            return redirect(url_for('auth.list_users'))

        if request.method == 'POST':
            role = (request.form.get('role') or 'user').strip().lower()
            country = (request.form.get('country') or '').strip().upper() or None
            active = 'active' in request.form

            # Não permitir desativar o próprio usuário
            if user_id == int(current_user.get_id()) and not active:
                flash('Você não pode desativar seu próprio usuário.', 'danger')
                return render_template('auth/edit_user.html', user=user.raw)

            try:
                auth_service.update_user(user_id, role=role, country=country, active=active)
                flash('Usuário atualizado com sucesso!', 'success')
                return redirect(url_for('auth.list_users'))
            except ValueError as exc:
                flash(str(exc), 'danger')

        return render_template('auth/edit_user.html', user=user.raw)

    return bp
