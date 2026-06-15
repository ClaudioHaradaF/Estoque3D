import os
import logging
from flask import Flask, render_template, current_app
from app.config import Config
from app.extensions import db, migrate, csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000

    if not app.config.get('SECRET_KEY'):
        raise RuntimeError(
            "SECRET_KEY não configurada. Defina a variável de ambiente SECRET_KEY "
            "ou crie um arquivo .env com SECRET_KEY=sua-chave-secreta-aqui"
        )

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    app.logger.info('Aplicacao Estoque3D iniciada')

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
    from app.routes.configuracoes import bp as configuracoes_bp
    from app.routes.search import bp as search_bp

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
    app.register_blueprint(configuracoes_bp)
    app.register_blueprint(search_bp)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    with app.app_context():
        from app.models import categoria, insumo, produto, produto_insumo, venda, venda_item, usuario, catalogo, meta, taxa_configuracao
        db.create_all()

        from app.models.usuario import Usuario
        if not Usuario.query.first():
            admin_email = app.config['ADMIN_EMAIL']
            admin = Usuario(email=admin_email)
            admin.set_password(app.config['ADMIN_PASSWORD'])
            admin.is_admin = True
            db.session.add(admin)
            db.session.commit()
            app.logger.info('Admin criado: %s', admin_email)

        from app.models.taxa_configuracao import TaxaConfiguracao
        if not TaxaConfiguracao.query.first():
            padrao = {
                'dinheiro': 0,
                'credito': 2.5,
                'debito': 1.2,
                'pix': 0,
            }
            for metodo, taxa in padrao.items():
                db.session.add(TaxaConfiguracao(forma_pagamento=metodo, taxa_percentual=taxa))
            db.session.commit()
            app.logger.info('Taxas padrao criadas')

    @app.before_request
    def proteger_rotas():
        from flask import request, session, redirect, url_for, flash
        if not request.endpoint:
            return
        if request.endpoint == 'static':
            return
        if request.endpoint.startswith('auth.'):
            return
        if request.endpoint == 'offline':
            return
        if 'user_id' not in session:
            flash('Faça login para acessar o sistema.', 'warning')
            return redirect(url_for('auth.login', next=request.path))

    @app.route('/offline')
    def offline():
        return render_template('offline.html'), 200

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('404.html'), 403

    @app.context_processor
    def inject_baixo_estoque():
        from app.models.produto import Produto
        limite = current_app.config['ESTOQUE_BAIXO_LIMITE']
        alerta = current_app.config['ESTOQUE_BAIXO_ALERTA']
        qtd = Produto.query.filter(Produto.ativo == True, Produto.qtd_estoque <= limite).count()
        return {
            'baixo_estoque_count': qtd,
            'ESTOQUE_BAIXO_LIMITE': limite,
            'ESTOQUE_BAIXO_ALERTA': alerta,
        }

    return app
