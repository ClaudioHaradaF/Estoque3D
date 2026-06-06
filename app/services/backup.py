import os
import shutil
from datetime import datetime

BACKUP_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'instance', 'backups'
)
DB_PATH = os.path.join(
    os.path.dirname(BACKUP_DIR), 'estoque3d.db'
)
MAX_BACKUPS = 7


def _limpar_antigos():
    if not os.path.exists(BACKUP_DIR):
        return
    backups = sorted([
        os.path.join(BACKUP_DIR, f)
        for f in os.listdir(BACKUP_DIR)
        if f.endswith('.db')
    ], key=os.path.getmtime)
    while len(backups) > MAX_BACKUPS:
        os.remove(backups.pop(0))


def criar_backup():
    if not os.path.exists(DB_PATH):
        return None
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nome = f'estoque3d_{timestamp}.db'
    destino = os.path.join(BACKUP_DIR, nome)
    shutil.copy2(DB_PATH, destino)
    _limpar_antigos()
    return nome


def listar_backups():
    if not os.path.exists(BACKUP_DIR):
        return []
    backups = sorted([
        f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')
    ], reverse=True)
    resultado = []
    for b in backups:
        path = os.path.join(BACKUP_DIR, b)
        size = os.path.getsize(path)
        resultado.append({
            'nome': b,
            'tamanho': size,
            'data': datetime.fromtimestamp(os.path.getmtime(path))
        })
    return resultado
