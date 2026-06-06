from app.extensions import db


class VendaItem(db.Model):
    __tablename__ = 'venda_item'

    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('venda.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    qtd = db.Column(db.Integer, nullable=False, default=1)
    preco_unitario = db.Column(db.Float, nullable=False)
    custo_unitario = db.Column(db.Float, nullable=False, default=0)

    produto = db.relationship('Produto', lazy='joined')

    @property
    def subtotal(self):
        return round(self.preco_unitario * self.qtd, 2)

    @property
    def lucro_item(self):
        return round((self.preco_unitario - self.custo_unitario) * self.qtd, 2)

    def __repr__(self):
        return f'<VendaItem v={self.venda_id} p={self.produto_id}>'
