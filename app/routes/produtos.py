import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from app.extensions import db
from app.models.produto import Produto
from app.models.categoria import Categoria
from app.models.insumo import Insumo
from app.models.produto_insumo import ProdutoInsumo
from app.models.venda_item import VendaItem

bp = Blueprint('produtos', __name__)

EXTENSOES_PERMITIDAS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def arquivo_permitido(nome):
    return '.' in nome and nome.rsplit('.', 1)[1].lower() in EXTENSOES_PERMITIDAS


@bp.route('/')
def listar():
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = request.args.get('por_pagina', 24, type=int)
    busca = request.args.get('busca', '').strip()
    categoria_id = request.args.get('categoria_id', '').strip()
    query = Produto.query.filter_by(ativo=True)
    if busca:
        query = query.filter(Produto.nome.ilike(f'%{busca}%'))
    if categoria_id:
        query = query.filter_by(categoria_id=int(categoria_id))
    pagination = query.order_by(Produto.nome).paginate(
        page=pagina, per_page=por_pagina, error_out=False
    )
    produtos = pagination.items
    categorias = Categoria.query.order_by(Categoria.nome).all()
    return render_template(
        'produtos/listar.html', produtos=produtos, pagination=pagination,
        categorias=categorias, busca=busca, cat_filtro=categoria_id
    )


@bp.route('/<int:id>')
def detalhes(id):
    produto = Produto.query.get_or_404(id)
    return render_template('produtos/detalhes.html', produto=produto)


@bp.route('/novo', methods=['GET', 'POST'])
def novo():
    categorias = Categoria.query.order_by(Categoria.nome).all()
    insumos = Insumo.query.order_by(Insumo.nome).all()
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        if not nome:
            flash('O nome do produto é obrigatório.', 'danger')
            return render_template('produtos/form.html', produto=None, categorias=categorias, insumos=insumos)
        try:
            preco_venda = float(request.form.get('preco_venda', 0))
        except ValueError:
            preco_venda = 0
        try:
            peso = float(request.form.get('peso', 0)) if request.form.get('peso') else None
        except ValueError:
            peso = None
        try:
            qtd_estoque = int(request.form.get('qtd_estoque', 0))
        except ValueError:
            qtd_estoque = 0
        categoria_id = request.form.get('categoria_id', type=int) or None
        descricao = request.form.get('descricao', '').strip()
        try:
            tempo_impressao = float(request.form.get('tempo_impressao', 0))
        except ValueError:
            tempo_impressao = 0
        try:
            custo_maquina_hora = float(request.form.get('custo_maquina_hora', 1.50))
        except ValueError:
            custo_maquina_hora = 1.50
        try:
            custo_energia_hora = float(request.form.get('custo_energia_hora', 0.75))
        except ValueError:
            custo_energia_hora = 0.75
        try:
            custo_mao_obra_hora = float(request.form.get('custo_mao_obra_hora', 0))
        except ValueError:
            custo_mao_obra_hora = 0
        try:
            custo_material_lote = float(request.form.get('custo_material_lote', 0))
        except ValueError:
            custo_material_lote = 0
        try:
            qtd_por_lote = int(request.form.get('qtd_por_lote', 1))
        except ValueError:
            qtd_por_lote = 1

        produto = Produto(
            nome=nome, preco_venda=preco_venda, peso=peso,
            categoria_id=categoria_id, qtd_estoque=qtd_estoque,
            descricao=descricao, tempo_impressao=tempo_impressao,
            custo_maquina_hora=custo_maquina_hora,
            custo_energia_hora=custo_energia_hora,
            custo_mao_obra_hora=custo_mao_obra_hora,
            custo_material_lote=custo_material_lote,
            qtd_por_lote=qtd_por_lote,
        )
        db.session.add(produto)
        db.session.flush()

        imagem = request.files.get('imagem')
        if imagem and imagem.filename:
            if arquivo_permitido(imagem.filename):
                nome_arquivo = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(imagem.filename)}"
                caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], nome_arquivo)
                imagem.save(caminho)
                produto.imagem = nome_arquivo
            else:
                flash('Formato de imagem não permitido.', 'warning')

        ids_insumos = request.form.getlist('insumo_id')
        quantidades = request.form.getlist('insumo_qtd')
        for iid, qtd in zip(ids_insumos, quantidades):
            try:
                insumo_id = int(iid)
                qtd_usada = float(qtd) if qtd else 1
            except ValueError:
                continue
            if qtd_usada > 0:
                pi = ProdutoInsumo(produto_id=produto.id, insumo_id=insumo_id, qtd_usada=qtd_usada)
                db.session.add(pi)

        produto.recalcular_custo()
        db.session.commit()
        flash('Produto cadastrado com sucesso!', 'success')
        return redirect(url_for('produtos.listar'))
    return render_template('produtos/form.html', produto=None, categorias=categorias, insumos=insumos)


@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    produto = Produto.query.get_or_404(id)
    categorias = Categoria.query.order_by(Categoria.nome).all()
    insumos = Insumo.query.order_by(Insumo.nome).all()
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        if not nome:
            flash('O nome do produto é obrigatório.', 'danger')
            return render_template('produtos/form.html', produto=produto, categorias=categorias, insumos=insumos)
        try:
            preco_venda = float(request.form.get('preco_venda', 0))
        except ValueError:
            preco_venda = 0
        try:
            peso = float(request.form.get('peso', 0)) if request.form.get('peso') else None
        except ValueError:
            peso = None
        try:
            qtd_estoque = int(request.form.get('qtd_estoque', 0))
        except ValueError:
            qtd_estoque = 0
        categoria_id = request.form.get('categoria_id', type=int) or None
        descricao = request.form.get('descricao', '').strip()
        try:
            tempo_impressao = float(request.form.get('tempo_impressao', 0))
        except ValueError:
            tempo_impressao = 0
        try:
            custo_maquina_hora = float(request.form.get('custo_maquina_hora', 1.50))
        except ValueError:
            custo_maquina_hora = 1.50
        try:
            custo_energia_hora = float(request.form.get('custo_energia_hora', 0.75))
        except ValueError:
            custo_energia_hora = 0.75
        try:
            custo_mao_obra_hora = float(request.form.get('custo_mao_obra_hora', 0))
        except ValueError:
            custo_mao_obra_hora = 0
        try:
            custo_material_lote = float(request.form.get('custo_material_lote', 0))
        except ValueError:
            custo_material_lote = 0
        try:
            qtd_por_lote = int(request.form.get('qtd_por_lote', 1))
        except ValueError:
            qtd_por_lote = 1

        produto.nome = nome
        produto.preco_venda = preco_venda
        produto.peso = peso
        produto.categoria_id = categoria_id
        produto.qtd_estoque = qtd_estoque
        produto.descricao = descricao
        produto.tempo_impressao = tempo_impressao
        produto.custo_maquina_hora = custo_maquina_hora
        produto.custo_energia_hora = custo_energia_hora
        produto.custo_mao_obra_hora = custo_mao_obra_hora
        produto.custo_material_lote = custo_material_lote
        produto.qtd_por_lote = qtd_por_lote

        imagem = request.files.get('imagem')
        if imagem and imagem.filename:
            if arquivo_permitido(imagem.filename):
                nome_arquivo = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(imagem.filename)}"
                caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], nome_arquivo)
                imagem.save(caminho)
                if produto.imagem:
                    caminho_antigo = os.path.join(current_app.config['UPLOAD_FOLDER'], produto.imagem)
                    if os.path.exists(caminho_antigo):
                        os.remove(caminho_antigo)
                produto.imagem = nome_arquivo
            else:
                flash('Formato de imagem não permitido.', 'warning')

        ProdutoInsumo.query.filter_by(produto_id=produto.id).delete()
        ids_insumos = request.form.getlist('insumo_id')
        quantidades = request.form.getlist('insumo_qtd')
        for iid, qtd in zip(ids_insumos, quantidades):
            try:
                insumo_id = int(iid)
                qtd_usada = float(qtd) if qtd else 1
            except ValueError:
                continue
            if qtd_usada > 0:
                pi = ProdutoInsumo(produto_id=produto.id, insumo_id=insumo_id, qtd_usada=qtd_usada)
                db.session.add(pi)

        produto.recalcular_custo()
        db.session.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('produtos.listar'))
    return render_template('produtos/form.html', produto=produto, categorias=categorias, insumos=insumos)


@bp.route('/<int:id>/duplicar', methods=['POST'])
def duplicar(id):
    original = Produto.query.get_or_404(id)
    novo = Produto(
        nome=f"{original.nome} (cópia)",
        preco_venda=original.preco_venda,
        peso=original.peso,
        categoria_id=original.categoria_id,
        qtd_estoque=0,
        descricao=original.descricao,
        tempo_impressao=original.tempo_impressao,
        custo_maquina_hora=original.custo_maquina_hora,
        custo_energia_hora=original.custo_energia_hora,
        custo_mao_obra_hora=original.custo_mao_obra_hora,
        custo_material_lote=original.custo_material_lote,
        qtd_por_lote=original.qtd_por_lote,
        tamanho=original.tamanho,
    )
    db.session.add(novo)
    db.session.flush()

    for pi in original.insumos.all():
        db.session.add(ProdutoInsumo(
            produto_id=novo.id, insumo_id=pi.insumo_id, qtd_usada=pi.qtd_usada
        ))

    novo.recalcular_custo()
    db.session.commit()
    flash('Produto duplicado com sucesso!', 'success')
    return redirect(url_for('produtos.editar', id=novo.id))


@bp.route('/relatorio')
def relatorio():
    from datetime import datetime as dt
    produtos = Produto.query.filter_by(ativo=True).order_by(Produto.nome).all()
    return render_template('produtos/relatorio.html', produtos=produtos, now=lambda: dt.now())


@bp.route('/<int:id>/excluir', methods=['POST'])
def excluir(id):
    produto = Produto.query.get_or_404(id)
    if VendaItem.query.filter_by(produto_id=id).first():
        flash('Não é possível excluir produto que já foi vendido.', 'danger')
        return redirect(url_for('produtos.listar'))
    if produto.imagem:
        caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], produto.imagem)
        if os.path.exists(caminho):
            os.remove(caminho)
    db.session.delete(produto)
    db.session.commit()
    flash('Produto excluído com sucesso!', 'success')
    return redirect(url_for('produtos.listar'))
