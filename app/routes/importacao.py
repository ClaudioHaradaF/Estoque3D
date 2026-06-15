import time
from sqlalchemy.orm import subqueryload
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from unicodedata import normalize as ucnorm
from app.extensions import db
from app.models.produto import Produto
from app.models.categoria import Categoria
from app.models.venda import Venda
from app.models.venda_item import VendaItem
from app.services.gsheets import conectar, parsear_dados, exportar_dados

bp = Blueprint('importacao', __name__, url_prefix='/importar')


def _normalizar(nome):
    if not nome:
        return ''
    n = nome.strip().lower()
    n = ucnorm('NFKD', n)
    n = n.encode('ascii', errors='ignore').decode('ascii')
    n = n.replace('\u00b0', '').replace('\u00bd', '"').replace('"', '')
    n = n.replace('/', '').replace('\\', '')
    return n.strip()


@bp.route('/gsheets', methods=['GET', 'POST'])
def importar_gsheets():
    if request.method == 'GET':
        try:
            registros = conectar()
            dados, erros = parsear_dados(registros)
        except FileNotFoundError:
            flash('Arquivo de credenciais do Google Sheets não encontrado.', 'danger')
            return redirect(url_for('produtos.listar'))
        except Exception as e:
            flash(f'Erro ao conectar com Google Sheets: {e}', 'danger')
            return redirect(url_for('produtos.listar'))

        return render_template('produtos/importar_gsheets.html',
                               dados=dados, erros=erros, total=len(dados))

    if request.method == 'POST':
        try:
            registros = conectar()
            dados, erros = parsear_dados(registros)
        except Exception as e:
            flash(f'Erro ao conectar com Google Sheets: {e}', 'danger')
            return redirect(url_for('produtos.listar'))

        # Build normalized name lookup — busca TODOS os produtos, inclusive inativos
        todos_produtos = Produto.query.all()
        nome_map = {}
        for p in todos_produtos:
            key = _normalizar(p.nome)
            if key not in nome_map:
                nome_map[key] = p

        criados = 0
        atualizados = 0
        erros_item = []
        for item in dados:
            try:
                item_key = _normalizar(item.get('nome', ''))
                if not item_key:
                    erros_item.append('Item sem nome ignorado')
                    continue
                produto = nome_map.get(item_key)

                if item.get('nicho'):
                    if item.get('subnicho'):
                        nome_sub = f"{item['nicho']} > {item['subnicho']}"
                    else:
                        nome_sub = item['nicho']
                    cat = Categoria.query.filter_by(nome=nome_sub).first()
                    if not cat:
                        cat = Categoria(nome=nome_sub)
                        db.session.add(cat)
                        db.session.flush()
                else:
                    cat = None

                if produto:
                    produto.ordem = item['ordem']
                    produto.preco_venda = item['preco_venda']
                    produto.qtd_estoque = item['qtd_estoque']
                    produto.tamanho = item['tamanho'] or None
                    produto.descricao = item['descricao'] or None
                    produto.categoria_id = cat.id if cat else None
                    if not produto.ativo:
                        produto.ativo = True
                    atualizados += 1
                else:
                    produto = Produto(
                        ordem=item['ordem'],
                        nome=item['nome'],
                        preco_venda=item['preco_venda'],
                        qtd_estoque=item['qtd_estoque'],
                        tamanho=item['tamanho'] or None,
                        descricao=item['descricao'] or None,
                        categoria_id=cat.id if cat else None,
                    )
                    db.session.add(produto)
                    criados += 1
            except Exception as e:
                erros_item.append(f'Erro ao processar "{item.get("nome", "?")}": {e}')

        db.session.commit()
        erros.extend(erros_item)
        partes = []
        if criados:
            partes.append(f'{criados} criado(s)')
        if atualizados:
            partes.append(f'{atualizados} atualizado(s)')
        flash('Importação concluída! ' + ', '.join(partes) + '.', 'success')
        if erros:
            for e in erros[:5]:
                flash(e, 'warning')

        return redirect(url_for('produtos.listar'))


@bp.route('/exportar/gsheets', methods=['POST'])
def exportar_para_gsheets():
    ultima = session.get('ultima_exportacao', 0)
    if time.time() - ultima < 30:
        flash('Aguarde 30 segundos entre exportações.', 'warning')
        return redirect(url_for('produtos.listar'))
    try:
        todos = Produto.query.order_by(Produto.avulso, Produto.ordem).all()
        produtos_normais = [p for p in todos if not p.avulso]
        produtos_avulsos = [p for p in todos if p.avulso]
        vendas = Venda.query.options(
            subqueryload(Venda.itens).subqueryload(VendaItem.produto)
        ).order_by(Venda.data_venda.desc(), Venda.created_at.desc()).all()
        exportar_dados(produtos_normais, produtos_avulsos, vendas)
        session['ultima_exportacao'] = time.time()
        total_vendas = sum(len(v.itens) for v in vendas)
        flash(f'{len(produtos_normais)} produtos em Inventário, {len(produtos_avulsos)} avulsos, {total_vendas} itens em Vendas exportados!', 'success')
    except Exception as e:
        flash(f'Erro ao exportar para Google Sheets: {e}', 'danger')
    return redirect(url_for('produtos.listar'))
