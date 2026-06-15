from app.extensions import db


class ProdutoInsumo(db.Model):
    __tablename__ = 'produto_insumo'

    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False, index=True)
    insumo_id = db.Column(db.Integer, db.ForeignKey('insumo.id'), nullable=False, index=True)
    qtd_usada = db.Column(db.Float, nullable=False, default=1)

    insumo_rel = db.relationship('Insumo', back_populates='produtos_vinculados', lazy='joined')

    def __repr__(self):
        return f'<ProdutoInsumo p={self.produto_id} i={self.insumo_id}>'
