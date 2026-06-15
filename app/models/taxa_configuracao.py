from datetime import datetime, timezone
from app.extensions import db


class TaxaConfiguracao(db.Model):
    __tablename__ = 'taxa_configuracao'

    id = db.Column(db.Integer, primary_key=True)
    forma_pagamento = db.Column(db.String(20), unique=True, nullable=False)
    taxa_percentual = db.Column(db.Float, nullable=False, default=0)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<TaxaConfiguracao {self.forma_pagamento}: {self.taxa_percentual}%>'
