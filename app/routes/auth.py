from urllib.parse import urlparse
from time import time
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.extensions import db
from app.models.usuario import Usuario

bp = Blueprint('auth', __name__, url_prefix='/auth')

MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300  # 5 minutos
LOCKOUT_DELAY_BASE = 1.0  # segundos, duplica a cada tentativa após 3


def _check_rate_limit() -> tuple[bool, float]:
    """Verifica se login está em cooldown. Retorna (pode_tentar, delay_restante)."""
    attempts = session.get('login_attempts', [])
    current_time = time()
    
    # Limpar tentativas expiradas
    attempts = [t for t in attempts if current_time - t < LOGIN_WINDOW_SECONDS]
    session['login_attempts'] = attempts
    
    if len(attempts) >= MAX_LOGIN_ATTEMPTS:
        delay = LOCKOUT_DELAY_BASE * (2 ** max(0, len(attempts) - 3))
        remaining = max(0, LOGIN_WINDOW_SECONDS - (current_time - attempts[0]))
        return False, max(delay, remaining)
    return True, 0


def _record_failed_attempt():
    """Registra tentativa falha."""
    attempts = session.get('login_attempts', [])
    attempts.append(time())
    session['login_attempts'] = attempts


def _clear_rate_limit():
    """Limpa limitador após login bem-sucedido."""
    session.pop('login_attempts', None)


def _url_segura(target):
    parsed = urlparse(target)
    return not parsed.netloc and not parsed.scheme


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('password', '')

        pode_tentar, delay = _check_rate_limit()
        if not pode_tentar:
            flash(f'Muitas tentativas falhas. Aguarde {int(delay)}s antes de tentar novamente.', 'warning')
            return render_template('auth/login.html')

        usuario = Usuario.query.filter_by(email=email).first()
        if not usuario or not usuario.check_password(senha):
            _record_failed_attempt()
            flash('E-mail ou senha inválidos.', 'danger')
            return render_template('auth/login.html')

        _clear_rate_limit()
        session['user_id'] = usuario.id
        session['user_email'] = usuario.email
        next_url = request.args.get('next')
        if next_url and _url_segura(next_url):
            return redirect(next_url)
        flash(f'Bem-vindo, {usuario.email}!', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    session.clear()
    flash('Sessão encerrada.', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/perfil', methods=['GET', 'POST'])
def perfil():
    usuario = Usuario.query.get(session.get('user_id'))
    if not usuario:
        flash('Faça login para acessar.', 'warning')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        senha_atual = request.form.get('senha_atual', '')
        nova_senha = request.form.get('nova_senha', '')
        confirmar = request.form.get('confirmar_senha', '')

        if not usuario.check_password(senha_atual):
            flash('Senha atual incorreta.', 'danger')
            return render_template('auth/perfil.html', usuario=usuario)

        if len(nova_senha) < 6:
            flash('Nova senha deve ter no mínimo 6 caracteres.', 'danger')
            return render_template('auth/perfil.html', usuario=usuario)

        if nova_senha != confirmar:
            flash('Confirmação de senha não confere.', 'danger')
            return render_template('auth/perfil.html', usuario=usuario)

        usuario.set_password(nova_senha)
        db.session.commit()
        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/perfil.html', usuario=usuario)
