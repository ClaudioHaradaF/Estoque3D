from datetime import datetime, timezone
from app.extensions import db


class Catalogo(db.Model):
    __tablename__ = 'catalogo'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False, unique=True)
    descricao = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    itens = db.relationship('CatalogoItem', back_populates='catalogo_rel',
                            lazy='select', cascade='all, delete-orphan',
                            order_by='CatalogoItem.id')

    def __repr__(self):
        return f'<Catalogo {self.nome}>'


class CatalogoItem(db.Model):
    __tablename__ = 'catalogo_item'

    id = db.Column(db.Integer, primary_key=True)
    catalogo_id = db.Column(db.Integer, db.ForeignKey('catalogo.id'), nullable=False, index=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False, index=True)
    preco_personalizado = db.Column(db.Float, nullable=True)

    catalogo_rel = db.relationship('Catalogo', back_populates='itens')
    produto = db.relationship('Produto', lazy='joined')

    @property
    def preco_exibido(self):
        return self.preco_personalizado if self.preco_personalizado is not None else self.produto.preco_venda

    def __repr__(self):
        return f'<CatalogoItem cat={self.catalogo_id} prod={self.produto_id}>'
