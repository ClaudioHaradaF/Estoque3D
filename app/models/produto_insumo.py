from app.extensions import db


class ProdutoInsumo(db.Model):
    __tablename__ = 'produto_insumo'

    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    insumo_id = db.Column(db.Integer, db.ForeignKey('insumo.id'), nullable=False)
    qtd_usada = db.Column(db.Float, nullable=False, default=1)

    def __repr__(self):
        return f'<ProdutoInsumo p={self.produto_id} i={self.insumo_id}>'
