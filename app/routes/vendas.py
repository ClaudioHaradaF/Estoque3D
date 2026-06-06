from datetime import date, timedelta, datetime
from sqlalchemy import func
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.extensions import db, csrf
from app.models.venda import Venda
from app.models.venda_item import VendaItem
from app.models.produto import Produto

bp = Blueprint('vendas', __name__)


@bp.route('/')
def listar():
    hoje = date.today()
    fim = datetime.strptime(request.args.get('data_fim', hoje.isoformat()), '%Y-%m-%d').date()
    ini = datetime.strptime(request.args.get(
        'data_ini', (hoje - timedelta(days=30)).isoformat()), '%Y-%m-%d').date()

    vendas = Venda.query.filter(
        Venda.data_venda >= ini, Venda.data_venda <= fim
    ).order_by(Venda.data_venda.desc(), Venda.created_at.desc()).all()

    return render_template('vendas/listar.html', vendas=vendas, data_ini=ini, data_fim=fim)


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
            try:
                produto_id = int(pid)
                qtd_venda = int(qtd)
                preco = float(pco)
            except ValueError:
                continue
            if qtd_venda <= 0:
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

        if venda.itens.count() == 0:
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
    venda = Venda.query.get_or_404(id)
    return render_template('vendas/detalhes.html', venda=venda)


@bp.route('/<int:id>/recibo')
def recibo(id):
    from datetime import datetime as dt
    venda = Venda.query.get_or_404(id)
    return render_template('vendas/recibo.html', venda=venda, now=lambda: dt.now())


@bp.route('/<int:id>/excluir', methods=['POST'])
def excluir(id):
    venda = Venda.query.get_or_404(id)
    for item in venda.itens.all():
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


@bp.route('/rapida')
def rapida():
    produtos_query = Produto.query.filter(
        Produto.ativo == True, Produto.qtd_estoque > 0
    ).order_by(Produto.nome).all()
    produtos = [{
        'id': p.id, 'nome': p.nome, 'preco_venda': p.preco_venda,
        'custo_producao': p.custo_producao, 'qtd_estoque': p.qtd_estoque,
        'imagem': p.imagem
    } for p in produtos_query]
    return render_template('vendas/rapida.html', produtos=produtos, hoje=date.today())


@bp.route('/rapida/finalizar', methods=['POST'])
@csrf.exempt
def rapida_finalizar():
    data = request.get_json()
    if not data:
        return jsonify({'erro': 'Dados inválidos'}), 400

    itens = data.get('itens', [])
    cliente = data.get('cliente', '').strip()
    forma_pgto = data.get('forma_pagamento', '').strip()

    if not itens:
        return jsonify({'erro': 'Nenhum item na venda'}), 400

    venda = Venda(
        data_venda=date.today(),
        cliente_nome=cliente or None,
        forma_pagamento=forma_pgto or None
    )
    db.session.add(venda)
    db.session.flush()

    for item in itens:
        try:
            produto_id = int(item['id'])
            qtd = int(item['qtd'])
            preco = float(item['preco'])
        except (ValueError, KeyError):
            continue
        if qtd <= 0:
            continue
        produto = Produto.query.get(produto_id)
        if not produto:
            continue
        if produto.qtd_estoque < qtd:
            return jsonify({'erro': f'Estoque insuficiente para "{produto.nome}"'}), 400

        vi = VendaItem(
            venda_id=venda.id, produto_id=produto_id,
            qtd=qtd, preco_unitario=preco,
            custo_unitario=produto.custo_producao
        )
        db.session.add(vi)
        produto.qtd_estoque -= qtd

    venda.recalcular_totais()
    db.session.commit()
    return jsonify({'ok': True, 'venda_id': venda.id, 'total': venda.valor_total})
