from flask import Flask
from app.config import Config
from app.extensions import db, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.categorias import bp as categorias_bp
    from app.routes.insumos import bp as insumos_bp
    from app.routes.produtos import bp as produtos_bp
    from app.routes.vendas import bp as vendas_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(categorias_bp, url_prefix='/categorias')
    app.register_blueprint(insumos_bp, url_prefix='/insumos')
    app.register_blueprint(produtos_bp, url_prefix='/produtos')
    app.register_blueprint(vendas_bp, url_prefix='/vendas')

    with app.app_context():
        from app.models import categoria, insumo, produto, produto_insumo, venda, venda_item
        db.create_all()

    return app
