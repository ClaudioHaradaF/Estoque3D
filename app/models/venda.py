from datetime import datetime, timezone, date
from app.extensions import db


class Venda(db.Model):
    __tablename__ = 'venda'

    id = db.Column(db.Integer, primary_key=True)
    data_venda = db.Column(db.Date, nullable=False, default=date.today)
    cliente_nome = db.Column(db.String(200), nullable=True)
    valor_total = db.Column(db.Float, nullable=False, default=0)
    lucro_total = db.Column(db.Float, nullable=False, default=0)
    observacao = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    itens = db.relationship('VendaItem', backref='venda_rel',
                            lazy='dynamic', cascade='all, delete-orphan')

    def recalcular_totais(self):
        total_valor = 0
        total_lucro = 0
        for item in self.itens.all():
            total_valor += item.preco_unitario * item.qtd
            total_lucro += (item.preco_unitario - item.custo_unitario) * item.qtd
        self.valor_total = round(total_valor, 2)
        self.lucro_total = round(total_lucro, 2)

    def __repr__(self):
        return f'<Venda {self.id} {self.data_venda}>'
