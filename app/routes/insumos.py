from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db, parse_float
from app.models.insumo import Insumo

bp = Blueprint('insumos', __name__)

UNIDADES = ['un', 'kg', 'g', 'm', 'cm', 'mm', 'l', 'ml', 'm²', 'pct']


@bp.route('/')
def listar():
    busca = request.args.get('busca', '').strip()
    query = Insumo.query
    if busca:
        query = query.filter(Insumo.nome.ilike(f'%{busca}%'))
    insumos = query.order_by(Insumo.nome).all()
    return render_template('insumos/listar.html', insumos=insumos, busca=busca, unidades=UNIDADES)


@bp.route('/novo', methods=['GET', 'POST'])
def novo():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        preco_custo = parse_float(request.form.get('preco_custo', 0))
        qtd_estoque = parse_float(request.form.get('qtd_estoque', 0))
        unidade = request.form.get('unidade', 'un')
        descricao = request.form.get('descricao', '').strip()
        if not nome:
            flash('O nome do insumo é obrigatório.', 'danger')
            return render_template('insumos/form.html', insumo=None, unidades=UNIDADES)
        insumo = Insumo(
            nome=nome, preco_custo=preco_custo,
            qtd_estoque=qtd_estoque, unidade=unidade, descricao=descricao
        )
        db.session.add(insumo)
        db.session.commit()
        flash('Insumo cadastrado com sucesso!', 'success')
        return redirect(url_for('insumos.listar'))
    return render_template('insumos/form.html', insumo=None, unidades=UNIDADES)


@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    insumo = Insumo.query.get_or_404(id)
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        preco_custo = parse_float(request.form.get('preco_custo', 0))
        qtd_estoque = parse_float(request.form.get('qtd_estoque', 0))
        unidade = request.form.get('unidade', 'un')
        descricao = request.form.get('descricao', '').strip()
        if not nome:
            flash('O nome do insumo é obrigatório.', 'danger')
            return render_template('insumos/form.html', insumo=insumo, unidades=UNIDADES)
        insumo.nome = nome
        insumo.preco_custo = preco_custo
        insumo.qtd_estoque = qtd_estoque
        insumo.unidade = unidade
        insumo.descricao = descricao
        db.session.commit()
        flash('Insumo atualizado com sucesso!', 'success')
        return redirect(url_for('insumos.listar'))
    return render_template('insumos/form.html', insumo=insumo, unidades=UNIDADES)


@bp.route('/<int:id>/excluir', methods=['POST'])
def excluir(id):
    insumo = Insumo.query.get_or_404(id)
    if insumo.produtos.count() > 0:
        flash('Não é possível excluir insumo vinculado a produtos.', 'danger')
        return redirect(url_for('insumos.listar'))
    db.session.delete(insumo)
    db.session.commit()
    flash('Insumo excluído com sucesso!', 'success')
    return redirect(url_for('insumos.listar'))
