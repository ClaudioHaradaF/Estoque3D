from functools import wraps
from typing import Callable, Any, Optional
from flask import session, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()


def parse_float(value: Any, default: float = 0.0) -> float:
    """Converte valor para float, retornando default em erro."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def parse_int(value: Any, default: int = 0) -> int:
    """Converte valor para int, retornando default em erro."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def parse_optional_float(value: Any) -> Optional[float]:
    """Converte valor para float nullable, retornando None em erro ou string vazia."""
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def login_required(f: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if 'user_id' not in session:
            flash('Faça login para acessar o sistema.', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if 'user_id' not in session:
            flash('Faça login para acessar.', 'warning')
            return redirect(url_for('auth.login'))
        from app.models.usuario import Usuario
        usuario = Usuario.query.get(session['user_id'])
        if not usuario or not usuario.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
