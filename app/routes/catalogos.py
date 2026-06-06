from datetime import datetime as dt
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.extensions import db
from app.models.catalogo import Catalogo, CatalogoItem
from app.models.produto import Produto

bp = Blueprint('catalogos', __name__, url_prefix='/catalogos')


@bp.route('/')
def listar():
    catalogos = Catalogo.query.order_by(Catalogo.created_at.desc()).all()
    return render_template('catalogos/listar.html', catalogos=catalogos)


@bp.route('/novo', methods=['GET', 'POST'])
def novo():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        descricao = request.form.get('descricao', '').strip()
        if not nome:
            flash('Nome do catálogo é obrigatório.', 'danger')
            return render_template('catalogos/form.html', catalogo=None)

        catalogo = Catalogo(nome=nome, descricao=descricao or None)
        db.session.add(catalogo)
        db.session.flush()

        produtos_ids = request.form.getlist('produto_id[]')
        precos = request.form.getlist('preco[]')
        for pid, pco in zip(produtos_ids, precos):
            try:
                produto_id = int(pid)
                preco = pco.strip()
                item = CatalogoItem(
                    catalogo_id=catalogo.id,
                    produto_id=produto_id,
                    preco_personalizado=float(preco) if preco else None
                )
                db.session.add(item)
            except (ValueError, TypeError):
                continue

        db.session.commit()
        flash(f'Catálogo "{catalogo.nome}" criado com sucesso!', 'success')
        return redirect(url_for('catalogos.ver', id=catalogo.id))

    return render_template('catalogos/form.html', catalogo=None)


@bp.route('/<int:id>')
def ver(id):
    catalogo = Catalogo.query.get_or_404(id)
    itens = catalogo.itens.all()
    return render_template('catalogos/ver.html', catalogo=catalogo, itens=itens, now=lambda: dt.now())


@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    catalogo = Catalogo.query.get_or_404(id)
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        descricao = request.form.get('descricao', '').strip()
        if not nome:
            flash('Nome do catálogo é obrigatório.', 'danger')
            return render_template('catalogos/form.html', catalogo=catalogo)

        catalogo.nome = nome
        catalogo.descricao = descricao or None

        CatalogoItem.query.filter_by(catalogo_id=catalogo.id).delete()
        db.session.flush()

        produtos_ids = request.form.getlist('produto_id[]')
        precos = request.form.getlist('preco[]')
        for pid, pco in zip(produtos_ids, precos):
            try:
                produto_id = int(pid)
                preco = pco.strip()
                item = CatalogoItem(
                    catalogo_id=catalogo.id,
                    produto_id=produto_id,
                    preco_personalizado=float(preco) if preco else None
                )
                db.session.add(item)
            except (ValueError, TypeError):
                continue

        db.session.commit()
        flash(f'Catálogo "{catalogo.nome}" atualizado!', 'success')
        return redirect(url_for('catalogos.ver', id=catalogo.id))

    itens = catalogo.itens.all()
    return render_template('catalogos/form.html', catalogo=catalogo, itens=itens)


@bp.route('/<int:id>/excluir', methods=['POST'])
def excluir(id):
    catalogo = Catalogo.query.get_or_404(id)
    db.session.delete(catalogo)
    db.session.commit()
    flash('Catálogo excluído.', 'success')
    return redirect(url_for('catalogos.listar'))


@bp.route('/api/produtos')
def api_produtos():
    busca = request.args.get('busca', '').strip()
    query = Produto.query.filter_by(ativo=True)
    if busca:
        query = query.filter(Produto.nome.ilike(f'%{busca}%'))
    produtos = query.order_by(Produto.nome).limit(50).all()
    return jsonify([{
        'id': p.id,
        'nome': p.nome,
        'preco_venda': p.preco_venda,
        'qtd_estoque': p.qtd_estoque,
        'categoria': p.categoria_nome,
        'imagem': p.imagem
    } for p in produtos])
