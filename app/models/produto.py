from datetime import datetime, timezone
from typing import Optional
from app.extensions import db


class Produto(db.Model):
    __tablename__ = 'produto'

    id: int = db.Column(db.Integer, primary_key=True)
    nome: str = db.Column(db.String(200), nullable=False, unique=True)
    preco_venda: float = db.Column(db.Float, nullable=False, default=0)
    peso: Optional[float] = db.Column(db.Float, nullable=True)
    categoria_id: Optional[int] = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=True, index=True)
    custo_producao: float = db.Column(db.Float, nullable=False, default=0)
    qtd_estoque: int = db.Column(db.Integer, nullable=False, default=0)
    descricao: Optional[str] = db.Column(db.Text, nullable=True)
    tempo_impressao: float = db.Column(db.Float, nullable=False, default=0)
    custo_maquina_hora: float = db.Column(db.Float, nullable=False, default=1.50)
    custo_energia_hora: float = db.Column(db.Float, nullable=False, default=0.75)
    custo_mao_obra_hora: float = db.Column(db.Float, nullable=False, default=0)
    custo_material_lote: float = db.Column(db.Float, nullable=False, default=0)
    qtd_por_lote: int = db.Column(db.Integer, nullable=False, default=1)
    ordem: Optional[int] = db.Column(db.Integer, default=0)
    tamanho: Optional[str] = db.Column(db.String(20), nullable=True)
    imagem: Optional[str] = db.Column(db.String(200), nullable=True)
    ativo: bool = db.Column(db.Boolean, default=True)
    avulso: bool = db.Column(db.Boolean, default=False)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.Index('ix_produto_ativo', 'ativo'),
    )

    categoria_rel = db.relationship('Categoria', back_populates='produtos', lazy='joined')

    insumos = db.relationship('ProdutoInsumo', backref='produto_rel',
                              lazy='dynamic', cascade='all, delete-orphan')

    @property
    def categoria_nome(self) -> str:
        return self.categoria_rel.nome if self.categoria_rel else '-'

    @property
    def custo_insumos_unitario(self) -> float:
        return round(sum(pi.insumo_rel.preco_custo * pi.qtd_usada for pi in self.insumos.all()), 2)

    @property
    def custo_operacao(self) -> float:
        return round((self.custo_maquina_hora + self.custo_energia_hora + self.custo_mao_obra_hora) * self.tempo_impressao, 2)

    @property
    def custo_lote(self) -> float:
        return round(self.custo_operacao + self.custo_material_lote, 2)

    @property
    def custo_unitario_sem_insumos(self) -> float:
        if self.qtd_por_lote > 0:
            return round(self.custo_lote / self.qtd_por_lote, 2)
        return self.custo_lote

    @property
    def margem_lucro(self) -> float:
        if self.custo_producao > 0 and self.preco_venda > 0:
            return round((self.preco_venda - self.custo_producao) / self.preco_venda * 100, 1)
        return 100.0 if self.custo_producao == 0 else 0.0

    @property
    def lucro_unitario(self) -> float:
        return round(self.preco_venda - self.custo_producao, 2)

    def recalcular_custo(self) -> None:
        self.custo_producao = round(self.custo_unitario_sem_insumos + self.custo_insumos_unitario, 2)

    def __repr__(self) -> str:
        return f'<Produto {self.nome}>'

