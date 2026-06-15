from flask import Blueprint, jsonify, request, url_for
from sqlalchemy import func
from app.extensions import db
from app.models.produto import Produto
from app.models.venda import Venda
from app.models.venda_item import VendaItem
from app.models.insumo import Insumo
from app.models.categoria import Categoria


bp = Blueprint('search', __name__, url_prefix='/api/search')


@bp.route('')
def search():
    q = request.args.get('q', '').strip().lower()
    if len(q) < 2:
        return jsonify([])

    results = []

    # Produtos (top 8)
    produtos = Produto.query.filter(
        Produto.ativo == True,
        Produto.nome.ilike(f'%{q}%')
    ).limit(8).all()
    for p in produtos:
        results.append({
            'type': 'produto',
            'typeLabel': 'Produto',
            'icon': 'box-seam',
            'label': p.nome,
            'sub': f'R$ {p.preco_venda:.2f} | Estoque: {p.qtd_estoque}',
            'url': url_for('produtos.detalhes', id=p.id),
        })

    # Vendas recentes (top 5)
    vendas = Venda.query.options(
        db.subqueryload(Venda.itens)
    ).filter(
        Venda.cliente_nome.isnot(None),
        Venda.cliente_nome != '',
        Venda.cliente_nome.ilike(f'%{q}%')
    ).order_by(Venda.created_at.desc()).limit(5).all()
    for v in vendas:
        results.append({
            'type': 'venda',
            'typeLabel': 'Venda',
            'icon': 'cart3',
            'label': f'#{v.id} - {v.cliente_nome}',
            'sub': f'R$ {v.valor_total:.2f} em {v.data_venda.strftime("%d/%m/%Y")}',
            'url': url_for('vendas.detalhes', id=v.id),
        })

    # Vendas por ID
    if q.isdigit():
        venda_id = int(q)
        v = Venda.query.get(venda_id)
        if v:
            results.append({
                'type': 'venda',
                'typeLabel': 'Venda',
                'icon': 'cart3',
                'label': f'#{v.id} - {v.cliente_nome or "Sem cliente"}',
                'sub': f'R$ {v.valor_total:.2f} em {v.data_venda.strftime("%d/%m/%Y")}',
                'url': url_for('vendas.detalhes', id=v.id),
            })

    # Insumos (top 3)
    insumos = Insumo.query.filter(
        Insumo.nome.ilike(f'%{q}%')
    ).limit(3).all()
    for i in insumos:
        results.append({
            'type': 'insumo',
            'typeLabel': 'Insumo',
            'icon': 'puzzle',
            'label': i.nome,
            'sub': f'R$ {i.preco_custo:.2f} | Estoque: {i.qtd_estoque} {i.unidade}',
            'url': url_for('insumos.listar'),
        })

    # Categorias (top 3)
    categorias = Categoria.query.filter(
        Categoria.nome.ilike(f'%{q}%')
    ).limit(3).all()
    for cat in categorias:
        results.append({
            'type': 'categoria',
            'typeLabel': 'Categoria',
            'icon': 'tags',
            'label': cat.nome,
            'sub': cat.descricao or '',
            'url': url_for('produtos.listar', categoria_id=cat.id),
        })

    return jsonify(results)