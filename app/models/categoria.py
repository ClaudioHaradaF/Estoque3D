from app.extensions import db


class Categoria(db.Model):
    __tablename__ = 'categoria'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text, nullable=True)

    produtos = db.relationship('Produto', back_populates='categoria_rel', lazy='dynamic')

    def __repr__(self):
        return f'<Categoria {self.nome}>'
