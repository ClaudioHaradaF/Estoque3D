from datetime import date, timedelta, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.extensions import db
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

    produtos = Produto.query.filter(
        Produto.ativo == True, Produto.qtd_estoque > 0
    ).order_by(Produto.nome).all()
    return render_template('vendas/nova.html', produtos=produtos, hoje=date.today())


@bp.route('/<int:id>')
def detalhes(id):
    venda = Venda.query.get_or_404(id)
    return render_template('vendas/detalhes.html', venda=venda)


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


@bp.route('/api/produto/<int:id>')
def api_produto(id):
    produto = Produto.query.get_or_404(id)
    return jsonify({
        'id': produto.id,
        'nome': produto.nome,
        'preco_venda': produto.preco_venda,
        'qtd_estoque': produto.qtd_estoque,
    })
