from datetime import date, timedelta, datetime
from sqlalchemy import func
from sqlalchemy.orm import subqueryload
from sqlalchemy.exc import IntegrityError
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.extensions import db, parse_float, parse_int
from app.models.venda import Venda
from app.models.venda_item import VendaItem
from app.models.produto import Produto
from app.models.categoria import Categoria
from app.models.taxa_configuracao import TaxaConfiguracao

bp = Blueprint('vendas', __name__)


@bp.route('/')
def listar():
    hoje = date.today()
    fim = datetime.strptime(request.args.get('data_fim', hoje.isoformat()), '%Y-%m-%d').date()
    ini = datetime.strptime(request.args.get(
        'data_ini', (hoje - timedelta(days=30)).isoformat()), '%Y-%m-%d').date()
    busca = request.args.get('busca', '').strip()

    query = Venda.query.filter(
        Venda.data_venda >= ini, Venda.data_venda <= fim
    )
    if busca:
        query = query.join(VendaItem).join(Produto).filter(
            Venda.cliente_nome.ilike(f'%{busca}%') |
            Produto.nome.ilike(f'%{busca}%')
        ).distinct()

    vendas = query.options(
        subqueryload(Venda.itens).subqueryload(VendaItem.produto)
    ).order_by(Venda.data_venda.desc(), Venda.created_at.desc()).all()

    return render_template('vendas/listar.html', vendas=vendas, data_ini=ini, data_fim=fim, busca=busca)


@bp.route('/nova', methods=['GET', 'POST'])
def nova():
    if request.method == 'POST':
        try:
            data_venda = datetime.strptime(request.form['data_venda'], '%Y-%m-%d').date()
        except (ValueError, KeyError):
            data_venda = date.today()
        cliente = request.form.get('cliente_nome', '').strip()
        observacao = request.form.get('observacao', '').strip()

        venda = Venda(data_venda=data_venda, cliente_nome=cliente or None, observacao=observacao or None)
        db.session.add(venda)
        db.session.flush()

        produtos_ids = request.form.getlist('produto_id[]')
        quantidades = request.form.getlist('quantidade[]')
        precos = request.form.getlist('preco[]')

        for pid, qtd, pco in zip(produtos_ids, quantidades, precos):
            produto_id = parse_int(pid)
            qtd_venda = parse_int(qtd)
            preco = parse_float(pco)
            if produto_id <= 0 or qtd_venda <= 0:
                continue
            produto = Produto.query.get(produto_id)
            if not produto:
                continue
            if produto.qtd_estoque < qtd_venda:
                flash(f'Estoque insuficiente para "{produto.nome}" (disponível: {produto.qtd_estoque})', 'danger')
                db.session.rollback()
                return redirect(url_for('vendas.nova'))

            item = VendaItem(
                venda_id=venda.id, produto_id=produto_id,
                qtd=qtd_venda, preco_unitario=preco,
                custo_unitario=produto.custo_producao
            )
            db.session.add(item)
            produto.qtd_estoque -= qtd_venda

        if len(venda.itens) == 0:
            flash('Adicione ao menos um produto à venda.', 'danger')
            db.session.rollback()
            return redirect(url_for('vendas.nova'))

        venda.recalcular_totais()
        db.session.commit()
        flash('Venda registrada com sucesso!', 'success')
        return redirect(url_for('vendas.detalhes', id=venda.id))

    produtos_query = Produto.query.filter(
        Produto.ativo == True, Produto.qtd_estoque > 0
    ).order_by(Produto.nome).all()
    produtos = [{'id': p.id, 'nome': p.nome, 'preco_venda': p.preco_venda, 'custo_producao': p.custo_producao, 'qtd_estoque': p.qtd_estoque} for p in produtos_query]
    return render_template('vendas/nova.html', produtos=produtos, hoje=date.today())


@bp.route('/<int:id>')
def detalhes(id):
    venda = Venda.query.options(
        subqueryload(Venda.itens).subqueryload(VendaItem.produto)
    ).get_or_404(id)
    return render_template('vendas/detalhes.html', venda=venda)


@bp.route('/<int:id>/recibo')
def recibo(id):
    from datetime import datetime as dt
    venda = Venda.query.get_or_404(id)
    return render_template('vendas/recibo.html', venda=venda, now=lambda: dt.now())


@bp.route('/<int:id>/excluir', methods=['POST'])
def excluir(id):
    venda = Venda.query.get_or_404(id)
    for item in venda.itens:
        produto = Produto.query.get(item.produto_id)
        if produto:
            produto.qtd_estoque += item.qtd
    db.session.delete(venda)
    db.session.commit()
    flash('Venda cancelada e estoque restaurado.', 'success')
    return redirect(url_for('vendas.listar'))


@bp.route('/api/preco-frequente/<int:produto_id>')
def api_preco_frequente(produto_id):
    preco = db.session.query(
        VendaItem.preco_unitario, func.count(VendaItem.id).label('total')
    ).join(Venda).filter(
        VendaItem.produto_id == produto_id
    ).group_by(VendaItem.preco_unitario
    ).order_by(func.count(VendaItem.id).desc()
    ).first()
    if preco:
        return jsonify({'preco': preco.preco_unitario})
    produto = Produto.query.get(produto_id)
    if produto:
        return jsonify({'preco': produto.preco_venda})
    return jsonify({'preco': 0})


@bp.route('/ranking')
def ranking():
    hoje = date.today()
    fim = datetime.strptime(request.args.get('data_fim', hoje.isoformat()), '%Y-%m-%d').date()
    ini = datetime.strptime(request.args.get(
        'data_ini', (hoje - timedelta(days=30)).isoformat()), '%Y-%m-%d').date()

    ranking = db.session.query(
        Produto.id, Produto.nome, Produto.preco_venda,
        func.sum(VendaItem.qtd).label('qtd_total'),
        func.sum(VendaItem.preco_unitario * VendaItem.qtd).label('valor_total')
    ).join(VendaItem, Produto.id == VendaItem.produto_id
    ).join(Venda, Venda.id == VendaItem.venda_id
    ).filter(Venda.data_venda >= ini, Venda.data_venda <= fim
    ).group_by(Produto.id, Produto.nome, Produto.preco_venda
    ).order_by(func.sum(VendaItem.qtd).desc()).all()

    return render_template('vendas/ranking.html', ranking=ranking, data_ini=ini, data_fim=fim)


@bp.route('/api/produto/<int:id>')
def api_produto(id):
    produto = Produto.query.get_or_404(id)
    return jsonify({
        'id': produto.id,
        'nome': produto.nome,
        'preco_venda': produto.preco_venda,
        'qtd_estoque': produto.qtd_estoque,
    })


@bp.route('/api/clientes')
def api_clientes():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    clientes = db.session.query(Venda.cliente_nome).filter(
        Venda.cliente_nome.isnot(None),
        Venda.cliente_nome != '',
        Venda.cliente_nome.ilike(f'%{q}%')
    ).distinct().limit(8).all()
    return jsonify([c[0] for c in clientes])


@bp.route('/rapida')
def rapida():
    produtos_query = Produto.query.filter_by(ativo=True).order_by(Produto.nome).all()
    produtos = [{
        'id': p.id, 'nome': p.nome, 'preco_venda': p.preco_venda,
        'custo_producao': p.custo_producao, 'qtd_estoque': p.qtd_estoque,
        'imagem': p.imagem
    } for p in produtos_query]
    return render_template('vendas/rapida.html', produtos=produtos, hoje=date.today())


@bp.route('/rapida/finalizar', methods=['POST'])
def rapida_finalizar():
    data = request.get_json()
    if not data:
        return jsonify({'erro': 'Dados inválidos'}), 400

    itens = data.get('itens', [])
    cliente = data.get('cliente', '').strip()
    forma_pgto = data.get('forma_pagamento', '').strip()
    observacao = data.get('observacao', '').strip()

    if not itens:
        return jsonify({'erro': 'Nenhum item na venda'}), 400

    venda = Venda(
        data_venda=date.today(),
        cliente_nome=cliente or None,
        forma_pagamento=forma_pgto or None,
        observacao=observacao or None
    )
    db.session.add(venda)
    db.session.flush()

    erros_itens = []

    for i, item in enumerate(itens):
        try:
            produto_id = parse_int(item['id'])
            qtd = parse_int(item['qtd'])
            preco = parse_float(item['preco'])
        except KeyError:
            erros_itens.append(f'Item {i + 1}: dados faltando')
            continue
        if produto_id <= 0 or qtd <= 0:
            erros_itens.append(f'Item {i + 1}: dados inválidos')
            continue
        produto = Produto.query.get(produto_id)
        if not produto:
            erros_itens.append(f'Item {i + 1}: produto não encontrado (ID {produto_id})')
            continue
        if not produto.avulso and produto.qtd_estoque < qtd:
            return jsonify({'erro': f'Estoque insuficiente para "{produto.nome}"'}), 400

        vi = VendaItem(
            venda_id=venda.id, produto_id=produto_id,
            qtd=qtd, preco_unitario=preco,
            custo_unitario=produto.custo_producao
        )
        db.session.add(vi)
        if not produto.avulso:
            produto.qtd_estoque -= qtd

    if not venda.itens:
        return jsonify({'erro': 'Nenhum item válido na venda'}), 400

    venda.recalcular_totais()

    if forma_pgto:
        cfg = TaxaConfiguracao.query.filter_by(forma_pagamento=forma_pgto).first()
        if cfg and cfg.taxa_percentual > 0:
            venda.taxa_percentual = cfg.taxa_percentual
            venda.taxa_valor = round(venda.valor_total * cfg.taxa_percentual / 100, 2)
            venda.lucro_total = round(venda.lucro_total - venda.taxa_valor, 2)

    db.session.commit()
    resposta = {'ok': True, 'venda_id': venda.id, 'total': venda.valor_total}
    if erros_itens:
        resposta['aviso'] = f'{len(erros_itens)} item(ns) ignorado(s)'
        resposta['erros_itens'] = erros_itens
    return jsonify(resposta)


@bp.route('/rapida/criar-avulso', methods=['POST'])
def criar_avulso():
    data = request.get_json()
    if not data:
        return jsonify({'erro': 'Dados inválidos'}), 400

    nome = data.get('nome', '').strip()
    preco = data.get('preco', 0)
    categoria_nome = data.get('categoria', '').strip()

    if not nome:
        return jsonify({'erro': 'Nome do produto é obrigatório'}), 400

    preco = parse_float(preco)

    categoria_id = None
    if categoria_nome:
        cat = Categoria.query.filter_by(nome=categoria_nome).first()
        if not cat:
            cat = Categoria(nome=categoria_nome)
            db.session.add(cat)
            db.session.flush()
        categoria_id = cat.id

    produto = Produto(
        nome=nome,
        preco_venda=preco,
        ativo=False,
        avulso=True,
        qtd_estoque=0,
        categoria_id=categoria_id,
    )
    db.session.add(produto)
    try:
        db.session.flush()
        produto.recalcular_custo()
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        for i in range(2, 100):
            novo_nome = f"{nome} ({i})"
            existente = Produto.query.filter_by(nome=novo_nome).first()
            if not existente:
                produto = Produto(
                    nome=novo_nome, preco_venda=preco,
                    ativo=False, avulso=True, qtd_estoque=0,
                    categoria_id=categoria_id,
                )
                db.session.add(produto)
                db.session.flush()
                produto.recalcular_custo()
                db.session.commit()
                return jsonify({'id': produto.id, 'nome': produto.nome, 'preco': produto.preco_venda})
        return jsonify({'erro': 'Muitos produtos com este nome.'}), 400

    return jsonify({'id': produto.id, 'nome': produto.nome, 'preco': produto.preco_venda})


@bp.route('/<int:id>/desfazer', methods=['POST'])
def desfazer(id):
    venda = Venda.query.get_or_404(id)
    for item in venda.itens:
        if item.produto and not item.produto.avulso:
            item.produto.qtd_estoque += item.qtd
    db.session.delete(venda)
    db.session.commit()
    return jsonify({'ok': True})
