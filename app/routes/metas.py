from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.extensions import db
from app.models.meta import Meta
from app.models.venda import Venda
from app.models.enums import TipoMeta, CategoriaMeta

bp = Blueprint('metas', __name__, url_prefix='/metas')


def recalcular_financeira(meta):
    if meta.categoria == CategoriaMeta.FINANCEIRO:
        total = db.session.query(db.func.sum(Venda.valor_total)).filter(
            Venda.data_venda >= meta.data_ini,
            Venda.data_venda <= meta.data_fim
        ).scalar() or 0
        meta.valor_atual = round(total, 2)


@bp.route('/', methods=['GET', 'POST'])
def listar():
    metas = Meta.query.order_by(Meta.concluida.asc(), Meta.data_fim.asc()).all()
    for m in metas:
        if not m.concluida:
            recalcular_financeira(m)
    return render_template('metas/listar.html', metas=metas)


@bp.route('/nova', methods=['GET', 'POST'])
def nova():
    if request.method == 'POST':
        tipo = request.form.get('tipo', '')
        descricao = request.form.get('descricao', '').strip()
        categoria = request.form.get('categoria', 'financeiro')
        valor_meta = request.form.get('valor_meta', '0')
        data_ini = request.form.get('data_ini', '')
        data_fim = request.form.get('data_fim', '')

        if not descricao or not data_ini:
            flash('Descrição e data inicial são obrigatórias.', 'danger')
            return render_template('metas/form.html', meta=None, hoje=date.today())

        try:
            d_ini = datetime.strptime(data_ini, '%Y-%m-%d').date()
        except ValueError:
            flash('Data inicial inválida.', 'danger')
            return render_template('metas/form.html', meta=None, hoje=date.today())

        if tipo == 'diaria':
            d_fim = d_ini
        else:
            try:
                d_fim = datetime.strptime(data_fim, '%Y-%m-%d').date() if data_fim else d_ini
            except ValueError:
                flash('Data final inválida.', 'danger')
                return render_template('metas/form.html', meta=None, hoje=date.today())

        try:
            v_meta = float(valor_meta)
        except ValueError:
            v_meta = 0

        meta = Meta(
            tipo=tipo, descricao=descricao, categoria=categoria,
            valor_meta=v_meta, data_ini=d_ini, data_fim=d_fim
        )
        recalcular_financeira(meta)
        db.session.add(meta)
        db.session.commit()
        flash('Meta criada com sucesso!', 'success')
        return redirect(url_for('metas.listar'))

    return render_template('metas/form.html', meta=None, hoje=date.today())


@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    meta = Meta.query.get_or_404(id)
    if request.method == 'POST':
        meta.tipo = request.form.get('tipo', meta.tipo)
        meta.descricao = request.form.get('descricao', '').strip()
        meta.categoria = request.form.get('categoria', 'financeiro')
        try:
            meta.valor_meta = float(request.form.get('valor_meta', 0))
        except ValueError:
            pass
        try:
            meta.data_ini = datetime.strptime(request.form.get('data_ini', ''), '%Y-%m-%d').date()
        except ValueError:
            pass
        if meta.tipo == TipoMeta.DIARIA:
            meta.data_fim = meta.data_ini
        else:
            try:
                meta.data_fim = datetime.strptime(request.form.get('data_fim', ''), '%Y-%m-%d').date()
            except ValueError:
                pass

        recalcular_financeira(meta)
        db.session.commit()
        flash('Meta atualizada!', 'success')
        return redirect(url_for('metas.listar'))

    return render_template('metas/form.html', meta=meta, hoje=date.today())


@bp.route('/<int:id>/excluir', methods=['POST'])
def excluir(id):
    meta = Meta.query.get_or_404(id)
    db.session.delete(meta)
    db.session.commit()
    flash('Meta excluída.', 'success')
    return redirect(url_for('metas.listar'))


@bp.route('/<int:id>/atualizar-valor', methods=['POST'])
def atualizar_valor(id):
    meta = Meta.query.get_or_404(id)
    try:
        meta.valor_atual = float(request.form.get('valor_atual', 0))
        db.session.commit()
        flash('Valor atual atualizado!', 'success')
    except ValueError:
        flash('Valor inválido.', 'danger')
    return redirect(url_for('metas.listar'))


@bp.route('/<int:id>/alternar', methods=['POST'])
def alternar(id):
    meta = Meta.query.get_or_404(id)
    meta.concluida = not meta.concluida
    db.session.commit()
    status = 'concluída' if meta.concluida else 'reativada'
    flash(f'Meta {status}!', 'success')
    return redirect(url_for('metas.listar'))
