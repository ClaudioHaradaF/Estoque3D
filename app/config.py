import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(os.path.dirname(basedir), '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
        os.path.dirname(basedir), 'instance', 'estoque3d.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'harborio3d@gmail.com')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    ESTOQUE_BAIXO_LIMITE = 5
    ESTOQUE_BAIXO_ALERTA = 10
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_PERMANENT = True
