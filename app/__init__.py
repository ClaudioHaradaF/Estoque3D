import os
from flask import Flask, render_template
from app.config import Config
from app.extensions import db, migrate, csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not app.config.get('SECRET_KEY'):
        raise RuntimeError(
            "SECRET_KEY não configurada. Defina a variável de ambiente SECRET_KEY "
            "ou crie um arquivo .env com SECRET_KEY=sua-chave-secreta-aqui"
        )

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    from app.routes.auth import bp as auth_bp
    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.categorias import bp as categorias_bp
    from app.routes.insumos import bp as insumos_bp
    from app.routes.produtos import bp as produtos_bp
    from app.routes.vendas import bp as vendas_bp
    from app.routes.importacao import bp as importacao_bp
    from app.routes.usuarios import bp as usuarios_bp
    from app.routes.catalogos import bp as catalogos_bp
    from app.routes.metas import bp as metas_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(categorias_bp, url_prefix='/categorias')
    app.register_blueprint(insumos_bp, url_prefix='/insumos')
    app.register_blueprint(produtos_bp, url_prefix='/produtos')
    app.register_blueprint(vendas_bp, url_prefix='/vendas')
    app.register_blueprint(importacao_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(catalogos_bp)
    app.register_blueprint(metas_bp)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    with app.app_context():
        from app.models import categoria, insumo, produto, produto_insumo, venda, venda_item, usuario, catalogo, meta
        db.create_all()

        from app.models.usuario import Usuario
        if not Usuario.query.first():
            admin_email = app.config['ADMIN_EMAIL']
            admin = Usuario(email=admin_email)
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin)
            db.session.commit()
            print(f'[INFO] Admin criado: {admin_email}')

    @app.before_request
    def proteger_rotas():
        from flask import request, session, redirect, url_for, flash
        if not request.endpoint:
            return
        if request.endpoint == 'static':
            return
        if request.endpoint.startswith('auth.'):
            return
        if 'user_id' not in session:
            flash('Faça login para acessar o sistema.', 'warning')
            return redirect(url_for('auth.login', next=request.path))

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('404.html'), 403

    return app
