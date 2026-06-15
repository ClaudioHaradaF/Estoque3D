import os
import re
import gspread
from google.oauth2.service_account import Credentials

SCOPE = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1vDBjN943QILRqrQacNXBCbYGhuQlXj9jER3iDAXsCuE'
SHEET_NAME = 'Inventário'
CREDS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', '..', 'Estoque3D_creds', 'google-creds.json'
)


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


def exportar_dados(produtos_normais, produtos_avulsos, vendas):
    client = _get_client()
    sheet = client.open_by_key(SPREADSHEET_ID)

    ws_inv = sheet.worksheet(SHEET_NAME)
    _escrever_inventario(ws_inv, produtos_normais)

    try:
        ws_avul = sheet.worksheet('Avulsos')
    except gspread.WorksheetNotFound:
        ws_avul = sheet.add_worksheet('Avulsos', 100, 3)
        ws_avul.update('A1:C1', [['Nome', 'Preço', 'Observações']],
                       value_input_option='USER_ENTERED')
    _escrever_avulsos(ws_avul, produtos_avulsos)

    try:
        ws_vendas = sheet.worksheet('Vendas')
        if ws_vendas.col_count < 9:
            ws_vendas.add_cols(9 - ws_vendas.col_count)
        ws_vendas.update('A1:I1', [['Data', 'Produto', 'Qtd', 'Valor Unit.', 'Total', 'Forma Pagto.', 'Taxa %', 'Taxa R$', 'Valor Líquido']],
                        value_input_option='USER_ENTERED')
    except gspread.WorksheetNotFound:
        ws_vendas = sheet.add_worksheet('Vendas', 1000, 9)
        ws_vendas.update('A1:I1', [['Data', 'Produto', 'Qtd', 'Valor Unit.', 'Total', 'Forma Pagto.', 'Taxa %', 'Taxa R$', 'Valor Líquido']],
                        value_input_option='USER_ENTERED')
    _escrever_vendas(ws_vendas, vendas)


def _escrever_inventario(ws, produtos):
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
        updates.append({'range': f'F{i}', 'values': [[f'=IFERROR(SUMIF(Vendas!B:B;C{i};Vendas!C:C);0)']]})
        updates.append({'range': f'G{i}', 'values': [[f'=MAX(0;E{i}-F{i})']]})
        updates.append({'range': f'H{i}', 'values': [[p.preco_venda]]})
        updates.append({'range': f'I{i}', 'values': [[f'=G{i}*H{i}']]})
        updates.append({'range': f'J{i}', 'values': [[f'=F{i}*H{i}']]})
        updates.append({'range': f'K{i}', 'values': [[p.descricao or '']]})

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
    ws.batch_update(updates, value_input_option='USER_ENTERED')


def _escrever_avulsos(ws, produtos):
    updates = []
    for i, p in enumerate(produtos, start=2):
        updates.append({'range': f'A{i}', 'values': [[p.nome]]})
        updates.append({'range': f'B{i}', 'values': [[p.preco_venda]]})
        updates.append({'range': f'C{i}', 'values': [[p.descricao or '']]})
    total_row = len(produtos) + 2
    updates.append({'range': f'C{total_row}', 'values': [[f'{len(produtos)} produto(s) avulso(s)']]})
    ws.batch_update(updates, value_input_option='USER_ENTERED')


def _escrever_vendas(ws, vendas):
    from collections import defaultdict

    dias = defaultdict(list)
    for v in vendas:
        dias[v.data_venda].append(v)
    dates = sorted(dias.keys(), reverse=True)

    updates = []
    row = 2
    total_qtd = 0
    total_valor = 0.0
    total_taxa = 0.0
    cats = defaultdict(lambda: {'qtd': 0, 'total': 0.0})

    for data in dates:
        vendas_do_dia = dias[data]
        data_str = data.strftime('%d/%m/%Y')
        dia_qtd = 0
        dia_valor = 0.0

        for venda in vendas_do_dia:
            taxa_pct = venda.taxa_percentual or 0
            for item in venda.itens:
                nome_prod = item.produto.nome if item.produto else 'Produto removido'
                total_item = round(item.preco_unitario * item.qtd, 2)
                taxa_item = round(total_item * taxa_pct / 100, 2)
                liquido = round(total_item - taxa_item, 2)

                updates.append({'range': f'A{row}', 'values': [[data_str]]})
                updates.append({'range': f'B{row}', 'values': [[nome_prod]]})
                updates.append({'range': f'C{row}', 'values': [[item.qtd]]})
                updates.append({'range': f'D{row}', 'values': [[item.preco_unitario]]})
                updates.append({'range': f'E{row}', 'values': [[total_item]]})
                updates.append({'range': f'F{row}', 'values': [[venda.forma_pagamento or '']]})
                updates.append({'range': f'G{row}', 'values': [[f'{taxa_pct:.1f}%']]})
                updates.append({'range': f'H{row}', 'values': [[taxa_item]]})
                updates.append({'range': f'I{row}', 'values': [[liquido]]})

                dia_qtd += item.qtd
                dia_valor += total_item

                if item.produto and item.produto.categoria_rel:
                    cn = item.produto.categoria_rel.nome
                else:
                    cn = 'Sem categoria'
                cats[cn]['qtd'] += item.qtd
                cats[cn]['total'] += total_item

                row += 1

        dia_taxa = round(sum((v.taxa_valor or 0) for v in vendas_do_dia), 2)
        dia_liquido = round(dia_valor - dia_taxa, 2)

        updates.append({'range': f'A{row}', 'values': [['']]})
        updates.append({'range': f'B{row}', 'values': [[f'► Subtotal {data_str}']]})
        updates.append({'range': f'C{row}', 'values': [[dia_qtd]]})
        updates.append({'range': f'E{row}', 'values': [[round(dia_valor, 2)]]})
        updates.append({'range': f'H{row}', 'values': [[dia_taxa]]})
        updates.append({'range': f'I{row}', 'values': [[dia_liquido]]})
        row += 1

        total_qtd += dia_qtd
        total_valor += dia_valor
        total_taxa += dia_taxa

    row += 1
    total_liquido = round(total_valor - total_taxa, 2)
    updates.append({'range': f'B{row}', 'values': [[f'►► TOTAL GERAL']]})
    updates.append({'range': f'C{row}', 'values': [[total_qtd]]})
    updates.append({'range': f'E{row}', 'values': [[round(total_valor, 2)]]})
    updates.append({'range': f'H{row}', 'values': [[round(total_taxa, 2)]]})
    updates.append({'range': f'I{row}', 'values': [[total_liquido]]})
    row += 2

    updates.append({'range': f'A{row}', 'values': [['CATEGORIAS']]})
    row += 1
    updates.append({'range': f'A{row}', 'values': [['Categoria']]})
    updates.append({'range': f'C{row}', 'values': [['Qtd Vendida']]})
    updates.append({'range': f'E{row}', 'values': [['Valor Total']]})
    row += 1
    for cn in sorted(cats.keys()):
        cd = cats[cn]
        updates.append({'range': f'A{row}', 'values': [[cn]]})
        updates.append({'range': f'C{row}', 'values': [[cd['qtd']]]})
        updates.append({'range': f'E{row}', 'values': [[round(cd['total'], 2)]]})
        row += 1

    if updates:
        ws.batch_update(updates, value_input_option='USER_ENTERED')
