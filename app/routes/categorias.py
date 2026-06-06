from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db
from app.models.categoria import Categoria

bp = Blueprint('categorias', __name__)


@bp.route('/')
def listar():
    categorias = Categoria.query.order_by(Categoria.nome).all()
    return render_template('categorias/listar.html', categorias=categorias)


@bp.route('/novo', methods=['GET', 'POST'])
def novo():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        descricao = request.form.get('descricao', '').strip()
        if not nome:
            flash('O nome da categoria é obrigatório.', 'danger')
            return render_template('categorias/form.html', categoria=None)
        if Categoria.query.filter_by(nome=nome).first():
            flash('Já existe uma categoria com este nome.', 'danger')
            return render_template('categorias/form.html', categoria=None)
        cat = Categoria(nome=nome, descricao=descricao)
        db.session.add(cat)
        db.session.commit()
        flash('Categoria cadastrada com sucesso!', 'success')
        return redirect(url_for('categorias.listar'))
    return render_template('categorias/form.html', categoria=None)


@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    cat = Categoria.query.get_or_404(id)
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        descricao = request.form.get('descricao', '').strip()
        if not nome:
            flash('O nome da categoria é obrigatório.', 'danger')
            return render_template('categorias/form.html', categoria=cat)
        existente = Categoria.query.filter_by(nome=nome).first()
        if existente and existente.id != id:
            flash('Já existe uma categoria com este nome.', 'danger')
            return render_template('categorias/form.html', categoria=cat)
        cat.nome = nome
        cat.descricao = descricao
        db.session.commit()
        flash('Categoria atualizada com sucesso!', 'success')
        return redirect(url_for('categorias.listar'))
    return render_template('categorias/form.html', categoria=cat)


@bp.route('/<int:id>/excluir', methods=['POST'])
def excluir(id):
    cat = Categoria.query.get_or_404(id)
    if cat.produtos.count() > 0:
        flash('Não é possível excluir categoria com produtos vinculados.', 'danger')
        return redirect(url_for('categorias.listar'))
    db.session.delete(cat)
    db.session.commit()
    flash('Categoria excluída com sucesso!', 'success')
    return redirect(url_for('categorias.listar'))
