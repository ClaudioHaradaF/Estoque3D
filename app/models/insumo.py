from datetime import datetime, timezone
from app.extensions import db


class Insumo(db.Model):
    __tablename__ = 'insumo'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False, unique=True)
    preco_custo = db.Column(db.Float, nullable=False, default=0)
    qtd_estoque = db.Column(db.Float, nullable=False, default=0)
    unidade = db.Column(db.String(10), nullable=False, default='un')
    descricao = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    produtos_vinculados = db.relationship('ProdutoInsumo', back_populates='insumo_rel', lazy='dynamic')

    def __repr__(self):
        return f'<Insumo {self.nome}>'
