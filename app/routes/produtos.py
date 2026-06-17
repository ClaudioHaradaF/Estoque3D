import os
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from app.extensions import db, parse_float, parse_int, parse_optional_float
from app.models.produto import Produto
from app.models.categoria import Categoria
from app.models.insumo import Insumo
from app.models.produto_insumo import ProdutoInsumo
from app.models.venda_item import VendaItem

bp = Blueprint('produtos', __name__)

EXTENSOES_PERMITIDAS_IMAGEM = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def arquivo_permitido(nome):
    return '.' in nome and nome.rsplit('.', 1)[1].lower() in EXTENSOES_PERMITIDAS_IMAGEM


def validar_magic_bytes(arquivo) -> bool:
    """Verifica magic bytes da imagem usando Pillow (imghdr removido no Python 3.13+)."""
    try:
        header = arquivo.read(1024)
        arquivo.seek(0)
        from io import BytesIO
        img = Image.open(BytesIO(header))
        img.verify()
        return img.format and img.format.lower() in EXTENSOES_PERMITIDAS_IMAGEM
    except Exception:
        return False


def redimensionar_imagem(caminho, max_lado=1200, thumb_lado=200):
    """Redimensiona imagem para max_lado (maior lado) e gera thumbnail."""
    try:
        img = Image.open(caminho)
        img.thumbnail((max_lado, max_lado), Image.LANCZOS)
        img.save(caminho, optimize=True, quality=85)
        # Thumbnail
        pasta = os.path.dirname(caminho)
        nome, ext = os.path.splitext(os.path.basename(caminho))
        thumb_nome = f"{nome}_thumb{ext}"
        thumb_path = os.path.join(pasta, thumb_nome)
        thumb = img.copy()
        thumb.thumbnail((thumb_lado, thumb_lado), Image.LANCZOS)
        thumb.save(thumb_path, optimize=True, quality=80)
        return thumb_nome
    except Exception:
        return None


@bp.route('/')
def listar():
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = request.args.get('por_pagina', 24, type=int)
    busca = request.args.get('busca', '').strip()
    categoria_id = request.args.get('categoria_id', '').strip()
    ordenar = request.args.get('ordenar', 'nome')
    direcao = request.args.get('direcao', 'asc')
    query = Produto.query.filter(
        Produto.ativo == True,
        or_(Produto.avulso == False, Produto.avulso == None)
    )
    if busca:
        query = query.filter(Produto.nome.ilike(f'%{busca}%'))
    if categoria_id:
        query = query.filter_by(categoria_id=int(categoria_id))
    ordem_map = {
        'nome': Produto.nome,
        'preco': Produto.preco_venda,
        'estoque': Produto.qtd_estoque,
    }
    coluna = ordem_map.get(ordenar, Produto.nome)
    if direcao == 'desc':
        coluna = coluna.desc()
    pagination = query.order_by(coluna).paginate(
        page=pagina, per_page=por_pagina, error_out=False
    )
    produtos = pagination.items
    categorias = Categoria.query.order_by(Categoria.nome).all()
    avulso_count = Produto.query.filter_by(avulso=True).count()
    return render_template(
        'produtos/listar.html', produtos=produtos, pagination=pagination,
        categorias=categorias, busca=busca, cat_filtro=categoria_id,
        avulso_count=avulso_count, ordenar=ordenar, direcao=direcao
    )


@bp.route('/api/buscar')
def buscar_json():
    q = request.args.get('q', '').strip()
    ordenar = request.args.get('ordenar', 'nome')
    direcao = request.args.get('direcao', 'asc')
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = request.args.get('por_pagina', 24, type=int)
    limite = request.args.get('limite', 0, type=int)

    query = Produto.query.filter(
        Produto.ativo == True,
        or_(Produto.avulso == False, Produto.avulso == None)
    )
    if q:
        query = query.filter(Produto.nome.ilike(f'%{q}%'))

    ordem_map = {'nome': Produto.nome, 'preco': Produto.preco_venda, 'estoque': Produto.qtd_estoque}
    col = ordem_map.get(ordenar, Produto.nome)
    if direcao == 'desc':
        col = col.desc()

    if limite:
        items = query.order_by(col).limit(limite).all()
        return jsonify([{'id': p.id, 'nome': p.nome, 'preco': p.preco_venda, 'estoque': p.qtd_estoque} for p in items])

    pagination = query.order_by(col).paginate(page=pagina, per_page=por_pagina, error_out=False)
    return jsonify({
        'items': [{'id': p.id, 'nome': p.nome, 'preco': p.preco_venda, 'estoque': p.qtd_estoque,
                    'imagem': p.imagem or '', 'categoria': (p.categoria_nome or '')} for p in pagination.items],
        'pagina': pagination.page,
        'total_paginas': pagination.pages,
        'total': pagination.total,
    })


@bp.route('/avulsos')
def listar_avulsos():
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = request.args.get('por_pagina', 24, type=int)
    busca = request.args.get('busca', '').strip()
    query = Produto.query.filter_by(avulso=True)
    if busca:
        query = query.filter(Produto.nome.ilike(f'%{busca}%'))
    pagination = query.order_by(Produto.created_at.desc()).paginate(
        page=pagina, per_page=por_pagina, error_out=False
    )
    produtos = pagination.items
    categorias = Categoria.query.order_by(Categoria.nome).all()
    return render_template(
        'produtos/listar_avulsos.html', produtos=produtos, pagination=pagination,
        categorias=categorias, busca=busca
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
        preco_venda = parse_float(request.form.get('preco_venda', 0))
        peso = parse_optional_float(request.form.get('peso'))
        qtd_estoque = parse_int(request.form.get('qtd_estoque', 0))
        categoria_id = request.form.get('categoria_id', type=int) or None
        descricao = request.form.get('descricao', '').strip()
        tempo_impressao = parse_float(request.form.get('tempo_impressao', 0))
        custo_maquina_hora = parse_float(request.form.get('custo_maquina_hora', 1.50))
        custo_energia_hora = parse_float(request.form.get('custo_energia_hora', 0.75))
        custo_mao_obra_hora = parse_float(request.form.get('custo_mao_obra_hora', 0))
        custo_material_lote = parse_float(request.form.get('custo_material_lote', 0))
        qtd_por_lote = parse_int(request.form.get('qtd_por_lote', 1))

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
            if arquivo_permitido(imagem.filename) and validar_magic_bytes(imagem):
                nome_arquivo = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(imagem.filename)}"
                caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], nome_arquivo)
                imagem.save(caminho)
                produto.imagem = nome_arquivo
                redimensionar_imagem(caminho)
            else:
                flash('Formato de imagem não permitido ou arquivo inválido.', 'warning')

        ids_insumos = request.form.getlist('insumo_id')
        quantidades = request.form.getlist('insumo_qtd')
        for iid, qtd in zip(ids_insumos, quantidades):
            insumo_id = parse_int(iid)
            if not insumo_id:
                continue
            qtd_usada = parse_float(qtd, 1)
            if qtd_usada > 0:
                pi = ProdutoInsumo(produto_id=produto.id, insumo_id=insumo_id, qtd_usada=qtd_usada)
                db.session.add(pi)

        produto.recalcular_custo()
        try:
            db.session.commit()
            flash('Produto cadastrado com sucesso!', 'success')
            return redirect(url_for('produtos.listar'))
        except IntegrityError:
            db.session.rollback()
            flash('Já existe um produto com este nome.', 'danger')
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
        preco_venda = parse_float(request.form.get('preco_venda', 0))
        peso = parse_optional_float(request.form.get('peso'))
        qtd_estoque = parse_int(request.form.get('qtd_estoque', 0))
        categoria_id = request.form.get('categoria_id', type=int) or None
        descricao = request.form.get('descricao', '').strip()
        tempo_impressao = parse_float(request.form.get('tempo_impressao', 0))
        custo_maquina_hora = parse_float(request.form.get('custo_maquina_hora', 1.50))
        custo_energia_hora = parse_float(request.form.get('custo_energia_hora', 0.75))
        custo_mao_obra_hora = parse_float(request.form.get('custo_mao_obra_hora', 0))
        custo_material_lote = parse_float(request.form.get('custo_material_lote', 0))
        qtd_por_lote = parse_int(request.form.get('qtd_por_lote', 1))

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
            if arquivo_permitido(imagem.filename) and validar_magic_bytes(imagem):
                nome_arquivo = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(imagem.filename)}"
                caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], nome_arquivo)
                imagem.save(caminho)
                if produto.imagem:
                    caminho_antigo = os.path.join(current_app.config['UPLOAD_FOLDER'], produto.imagem)
                    thumb_antigo = os.path.join(current_app.config['UPLOAD_FOLDER'], produto.imagem.replace('.', '_thumb.'))
                    for p in [caminho_antigo, thumb_antigo]:
                        if os.path.exists(p):
                            os.remove(p)
                produto.imagem = nome_arquivo
                redimensionar_imagem(caminho)
            else:
                flash('Formato de imagem não permitido ou arquivo inválido.', 'warning')

        ProdutoInsumo.query.filter_by(produto_id=produto.id).delete()
        ids_insumos = request.form.getlist('insumo_id')
        quantidades = request.form.getlist('insumo_qtd')
        for iid, qtd in zip(ids_insumos, quantidades):
            insumo_id = parse_int(iid)
            if not insumo_id:
                continue
            qtd_usada = parse_float(qtd, 1)
            if qtd_usada > 0:
                pi = ProdutoInsumo(produto_id=produto.id, insumo_id=insumo_id, qtd_usada=qtd_usada)
                db.session.add(pi)

        # Se era avulso e agora tem dados completos, tornar catálogo
        if produto.avulso and produto.categoria_id:
            produto.avulso = False
            produto.ativo = True
        produto.recalcular_custo()
        try:
            db.session.commit()
            flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('produtos.listar'))
        except IntegrityError:
            db.session.rollback()
            flash('Já existe um produto com este nome.', 'danger')
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
    produtos = Produto.query.filter(
        Produto.ativo == True,
        or_(Produto.avulso == False, Produto.avulso == None)
    ).order_by(Produto.nome).all()
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
