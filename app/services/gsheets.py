import os
import re
import gspread
from google.oauth2.service_account import Credentials

SCOPE = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1vDBjN943QILRqrQacNXBCbYGhuQlXj9jER3iDAXsCuE'
SHEET_NAME = 'Inventário'
CREDS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'google-creds.json')


def parse_moeda(valor):
    if not valor:
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    limpo = re.sub(r'[R$\s]', '', str(valor)).replace('.', '').replace(',', '.')
    try:
        return float(limpo)
    except ValueError:
        return 0.0


def _get_client():
    if not os.path.exists(CREDS_PATH):
        raise FileNotFoundError(f'Arquivo de credenciais não encontrado: {CREDS_PATH}')
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPE)
    return gspread.authorize(creds)


def conectar():
    client = _get_client()
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    return sheet.get_all_records()


def parsear_dados(registros):
    produtos = []
    erros = []
    for i, row in enumerate(registros, start=2):
        nome = (row.get('Item') or '').strip()
        if not nome:
            erros.append(f'Linha {i}: Item sem nome, ignorado')
            continue
        try:
            produto = {
                'ordem': i,
                'nome': nome,
                'preco_venda': parse_moeda(row.get('Valor Unitário', 0)),
                'qtd_estoque': int(row.get('Estoque Atual', 0) or 0),
                'tamanho': (row.get('Tamanho') or '').strip(),
                'descricao': (row.get('Observações') or '').strip(),
                'nicho': (row.get('Nicho') or '').strip(),
                'subnicho': (row.get('Subnicho') or '').strip(),
            }
            produtos.append(produto)
        except (ValueError, TypeError) as e:
            erros.append(f'Linha {i} ({nome}): {e}')
    return produtos, erros


def exportar_dados(produtos):
    client = _get_client()
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

    # Get current sheet data to know how many rows exist
    existentes = sheet.get_all_values()
    num_linhas_existentes = len(existentes)  # includes header

    updates = []
    for i, p in enumerate(produtos, start=2):
        nicho = ''
        subnicho = ''
        if p.categoria_rel:
            partes = p.categoria_rel.nome.split(' > ', 1)
            nicho = partes[0]
            subnicho = partes[1] if len(partes) > 1 else ''

        updates.append({'range': f'A{i}', 'values': [[nicho]]})
        updates.append({'range': f'B{i}', 'values': [[subnicho]]})
        updates.append({'range': f'C{i}', 'values': [[p.nome]]})
        updates.append({'range': f'D{i}', 'values': [[p.tamanho or '']]})
        updates.append({'range': f'E{i}', 'values': [[p.qtd_estoque]]})
        updates.append({'range': f'H{i}', 'values': [[p.preco_venda]]})
        updates.append({'range': f'K{i}', 'values': [[p.descricao or '']]})

        # For NEW rows (beyond current sheet), write formulas too
        if i >= num_linhas_existentes:
            updates.append({'range': f'F{i}', 'values': [[f'=IFERROR(SUMIF(Vendas!B:B;C{i};Vendas!C:C);0)']]})
            updates.append({'range': f'G{i}', 'values': [[f'=MAX(0;E{i}-F{i})']]})
            updates.append({'range': f'I{i}', 'values': [[f'=G{i}*H{i}']]})
            updates.append({'range': f'J{i}', 'values': [[f'=F{i}*H{i}']]})

    # Add total row — clear data columns, write sum formulas
    ultima_linha = len(produtos) + 1
    total_row = ultima_linha + 1
    updates.append({'range': f'A{total_row}', 'values': [['']]})
    updates.append({'range': f'B{total_row}', 'values': [['']]})
    updates.append({'range': f'C{total_row}', 'values': [['']]})
    updates.append({'range': f'D{total_row}', 'values': [['']]})
    updates.append({'range': f'E{total_row}', 'values': [[f'=SUM(E2:E{ultima_linha})']]})
    updates.append({'range': f'F{total_row}', 'values': [[f'=SUM(F2:F{ultima_linha})']]})
    updates.append({'range': f'G{total_row}', 'values': [[f'=SUM(G2:G{ultima_linha})']]})
    updates.append({'range': f'H{total_row}', 'values': [['']]})
    updates.append({'range': f'I{total_row}', 'values': [[f'=SUM(I2:I{ultima_linha})']]})
    updates.append({'range': f'J{total_row}', 'values': [[f'=SUM(J2:J{ultima_linha})']]})
    updates.append({'range': f'K{total_row}', 'values': [['']]})

    sheet.batch_update(updates, value_input_option='USER_ENTERED')

    # Clear any rows beyond total_row (leftover from previous data)
    if num_linhas_existentes > total_row:
        start = total_row + 1
        end = num_linhas_existentes
        sheet.batch_clear([f'A{start}:K{end}'])
