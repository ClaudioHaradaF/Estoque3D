from flask import Blueprint, render_template, request, flash, redirect, url_for
from unicodedata import normalize as ucnorm
from app.extensions import db
from app.models.produto import Produto
from app.models.categoria import Categoria
from app.services.gsheets import conectar, parsear_dados, exportar_dados

bp = Blueprint('importacao', __name__, url_prefix='/importar')


def _normalizar(nome):
    """Remove acentos, sinais especiais (°, ½, ", etc.) e padroniza para matching."""
    n = nome.strip().lower()
    # Decompose unicode (é -> e + combining acute)
    n = ucnorm('NFKD', n)
    # Remove combining marks (accents, etc.)
    n = n.encode('ascii', errors='ignore').decode('ascii')
    # Replace special chars commonly used in this dataset
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

        # Build normalized name lookup for fuzzy matching
        todos_produtos = Produto.query.filter_by(ativo=True).all()
        nome_map = {}  # normalized name -> Produto
        for p in todos_produtos:
            key = _normalizar(p.nome)
            if key not in nome_map:
                nome_map[key] = p

        criados = 0
        atualizados = 0
        for item in dados:
            item_key = _normalizar(item['nome'])
            produto = nome_map.get(item_key)

            if item['nicho']:
                if item['subnicho']:
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
                produto.preco_venda = item['preco_venda']
                produto.qtd_estoque = item['qtd_estoque']
                produto.tamanho = item['tamanho'] or None
                produto.descricao = item['descricao'] or None
                produto.categoria_id = cat.id if cat else None
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

        db.session.commit()
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
    try:
        produtos = Produto.query.filter_by(ativo=True).order_by(Produto.ordem).all()
        exportar_dados(produtos)
        flash(f'{len(produtos)} produto(s) exportados para o Google Sheets com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao exportar para Google Sheets: {e}', 'danger')
    return redirect(url_for('produtos.listar'))
