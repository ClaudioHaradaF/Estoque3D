from datetime import datetime, timezone
from app.extensions import db


class Produto(db.Model):
    __tablename__ = 'produto'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    preco_venda = db.Column(db.Float, nullable=False, default=0)
    peso = db.Column(db.Float, nullable=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=True)
    custo_producao = db.Column(db.Float, nullable=False, default=0)
    qtd_estoque = db.Column(db.Integer, nullable=False, default=0)
    descricao = db.Column(db.Text, nullable=True)
    tempo_impressao = db.Column(db.Float, nullable=False, default=0)
    custo_maquina_hora = db.Column(db.Float, nullable=False, default=1.50)
    custo_energia_hora = db.Column(db.Float, nullable=False, default=0.75)
    custo_mao_obra_hora = db.Column(db.Float, nullable=False, default=0)
    custo_material_lote = db.Column(db.Float, nullable=False, default=0)
    qtd_por_lote = db.Column(db.Integer, nullable=False, default=1)
    imagem = db.Column(db.String(200), nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    insumos = db.relationship('ProdutoInsumo', backref='produto_rel',
                              lazy='dynamic', cascade='all, delete-orphan')

    @property
    def categoria_nome(self):
        return self.categoria_rel.nome if self.categoria_rel else '-'

    @property
    def custo_insumos_unitario(self):
        return round(sum(pi.insumo_rel.preco_custo * pi.qtd_usada for pi in self.insumos.all()), 2)

    @property
    def custo_operacao(self):
        return round((self.custo_maquina_hora + self.custo_energia_hora + self.custo_mao_obra_hora) * self.tempo_impressao, 2)

    @property
    def custo_lote(self):
        return round(self.custo_operacao + self.custo_material_lote, 2)

    @property
    def custo_unitario_sem_insumos(self):
        if self.qtd_por_lote > 0:
            return round(self.custo_lote / self.qtd_por_lote, 2)
        return self.custo_lote

    @property
    def margem_lucro(self):
        if self.custo_producao > 0 and self.preco_venda > 0:
            return round((self.preco_venda - self.custo_producao) / self.preco_venda * 100, 1)
        return 100.0 if self.custo_producao == 0 else 0.0

    @property
    def lucro_unitario(self):
        return round(self.preco_venda - self.custo_producao, 2)

    def recalcular_custo(self):
        self.custo_producao = round(self.custo_unitario_sem_insumos + self.custo_insumos_unitario, 2)

    def __repr__(self):
        return f'<Produto {self.nome}>'
