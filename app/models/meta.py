from datetime import datetime, timezone, date
from app.extensions import db
from app.models.enums import TipoMeta, CategoriaMeta
import sqlalchemy as sa


class Meta(db.Model):
    __tablename__ = 'meta'

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(sa.Enum(TipoMeta, values_callable=lambda x: [e.value for e in x]), nullable=False)
    descricao = db.Column(db.String(300), nullable=False)
    categoria = db.Column(sa.Enum(CategoriaMeta, values_callable=lambda x: [e.value for e in x]), nullable=False, default=CategoriaMeta.FINANCEIRO)
    valor_meta = db.Column(db.Float, nullable=False, default=0)
    valor_atual = db.Column(db.Float, nullable=False, default=0)
    data_ini = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    concluida = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def progresso(self):
        if self.valor_meta <= 0:
            return 0
        return min(round(self.valor_atual / self.valor_meta * 100, 1), 100)

    @property
    def atingida(self):
        return self.valor_atual >= self.valor_meta

    def __repr__(self):
        return f'<Meta {self.descricao[:30]} ({self.tipo})>'
