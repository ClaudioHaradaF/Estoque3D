from functools import wraps
from flask import session, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Faça login para acessar o sistema.', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Faça login para acessar.', 'warning')
            return redirect(url_for('auth.login'))
        from app.models.usuario import Usuario
        usuario = Usuario.query.get(session['user_id'])
        from flask import current_app
        if not usuario or usuario.email != current_app.config.get('ADMIN_EMAIL'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
