import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'estoque3d-chave-secreta')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
        os.path.dirname(basedir), 'instance', 'estoque3d.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
