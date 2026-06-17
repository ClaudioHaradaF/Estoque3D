from datetime import date, timedelta, datetime, timezone
from sqlalchemy import func
from sqlalchemy.orm import subqueryload
import os, csv, io
from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for, Response, current_app
from app.extensions import db
from app.models.produto import Produto
from app.models.insumo import Insumo
from app.models.categoria import Categoria
from app.models.venda import Venda
from app.models.venda_item import VendaItem
from app.models.meta import Meta

bp = Blueprint('dashboard', __name__)


def format_br(value):
    if value is None:
        return '0,00'
    return f'{value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


@bp.route('/')
def index():
    hoje = date.today()
    fim = datetime.strptime(request.args.get('data_fim', hoje.isoformat()), '%Y-%m-%d').date()
    ini = datetime.strptime(request.args.get(
        'data_ini', hoje.isoformat()), '%Y-%m-%d').date()

    total_produtos = Produto.query.filter_by(ativo=True).count()
    total_pecas = db.session.query(
        func.sum(Produto.qtd_estoque)
    ).filter(Produto.ativo == True).scalar() or 0
    total_insumos = Insumo.query.count()
    total_vendas = Venda.query.filter(
        Venda.data_venda >= ini, Venda.data_venda <= fim
    ).count()

    vendas_periodo = Venda.query.filter(
        Venda.data_venda >= ini, Venda.data_venda <= fim
    ).all()
    valor_periodo = sum(v.valor_total for v in vendas_periodo)
    lucro_periodo = sum(v.lucro_total for v in vendas_periodo)
    total_itens = db.session.query(func.sum(VendaItem.qtd)).join(Venda).filter(
        Venda.data_venda >= ini, Venda.data_venda <= fim
    ).scalar() or 0

    # Comparativo com período anterior
    dias_range = (fim - ini).days + 1
    ini_ant = ini - timedelta(days=dias_range)
    fim_ant = ini - timedelta(days=1)
    vendas_ant = Venda.query.filter(
        Venda.data_venda >= ini_ant, Venda.data_venda <= fim_ant
    ).all()
    valor_ant = sum(v.valor_total for v in vendas_ant)
    lucro_ant = sum(v.lucro_total for v in vendas_ant)
    var_faturamento = round((valor_periodo - valor_ant) / valor_ant * 100, 1) if valor_ant else None
    var_lucro = round((lucro_periodo - lucro_ant) / lucro_ant * 100, 1) if lucro_ant else None

    # Valor total em estoque (custo_producao * qtd_estoque)
    valor_estoque = db.session.query(
        func.sum(Produto.preco_venda * Produto.qtd_estoque)
    ).filter(Produto.ativo == True).scalar() or 0

    # Saúde do estoque
    ok_count = Produto.query.filter(Produto.ativo == True, Produto.qtd_estoque > current_app.config['ESTOQUE_BAIXO_ALERTA']).count()
    baixo_count = Produto.query.filter(Produto.ativo == True, Produto.qtd_estoque >= 1, Produto.qtd_estoque <= current_app.config['ESTOQUE_BAIXO_ALERTA']).count()
    zerado_count = Produto.query.filter(Produto.ativo == True, Produto.qtd_estoque == 0).count()

    # Ticket médio
    ticket_medio = round(valor_periodo / total_vendas, 2) if total_vendas > 0 else 0

    # Top 5 produtos mais vendidos no período (por quantidade)
    top_produtos = db.session.query(
        Produto.nome,
        func.sum(VendaItem.qtd).label('total_qtd'),
        func.sum(VendaItem.preco_unitario * VendaItem.qtd).label('total_valor')
    ).join(VendaItem, Produto.id == VendaItem.produto_id
    ).join(Venda, Venda.id == VendaItem.venda_id
    ).filter(Venda.data_venda >= ini, Venda.data_venda <= fim
    ).group_by(Produto.id, Produto.nome
    ).order_by(func.sum(VendaItem.qtd).desc()
    ).limit(5).all()

    top_prod_labels = [p.nome for p in top_produtos]
    top_prod_data = [float(p.total_qtd) for p in top_produtos]
    top_prod_valores = [float(p.total_valor) for p in top_produtos]

    # Últimas 5 vendas
    ultimas_vendas = Venda.query.options(
        subqueryload(Venda.itens)
    ).order_by(Venda.created_at.desc()).limit(5).all()

    produtos_baixo_estoque = Produto.query.filter(
        Produto.ativo == True, Produto.qtd_estoque <= current_app.config['ESTOQUE_BAIXO_LIMITE']
    ).order_by(Produto.qtd_estoque.asc()).all()

    categorias_count = db.session.query(
        Categoria.nome,
        func.count(Produto.id)
    ).outerjoin(Produto, db.and_(
        Categoria.id == Produto.categoria_id,
        Produto.ativo == True
    )).group_by(Categoria.id, Categoria.nome).all()
    cat_labels = [c[0] for c in categorias_count if c[1] > 0]
    cat_data = [c[1] for c in categorias_count if c[1] > 0]

    dias = (fim - ini).days
    vendas_diarias = {}
    for i in range(dias + 1):
        d = ini + timedelta(days=i)
        vendas_diarias[d.isoformat()] = 0

    for v in vendas_periodo:
        key = v.data_venda.isoformat()
        if key in vendas_diarias:
            vendas_diarias[key] += v.valor_total

    vendas_labels = sorted(vendas_diarias.keys())
    vendas_data = [vendas_diarias[k] for k in vendas_labels]

    # ===== Sparkline data (last 7 days) =====
    hoje_dt = date.today()
    spark_dates = [(hoje_dt - timedelta(days=i)) for i in range(6, -1, -1)]

    spark_vendas_list = []
    spark_faturamento_list = []
    spark_ini = spark_dates[0]
    spark_fim = spark_dates[-1]
    vendas_agrupadas = db.session.query(
        Venda.data_venda,
        func.count(Venda.id),
        func.coalesce(func.sum(Venda.valor_total), 0)
    ).filter(Venda.data_venda >= spark_ini, Venda.data_venda <= spark_fim
    ).group_by(Venda.data_venda).all()
    dia_map = {str(r[0]): (r[1], float(r[2])) for r in vendas_agrupadas}
    spark_vendas_list = [dia_map.get(d.isoformat(), (0, 0.0))[0] for d in spark_dates]
    spark_faturamento_list = [dia_map.get(d.isoformat(), (0, 0.0))[1] for d in spark_dates]

    spark_vendas = ','.join(str(x) for x in spark_vendas_list)
    spark_faturamento = ','.join(str(x) for x in spark_faturamento_list)

    spark_produtos_list = []
    spark_pecas_list = []
    spark_insumos_list = []

    # Load all created_at dates once and count cumulatively in Python
    produtos_created = [p.created_at for p in Produto.query.with_entities(Produto.created_at).filter(Produto.ativo == True).all()]
    insumos_created = [i.created_at for i in Insumo.query.with_entities(Insumo.created_at).all()]
    pecas_total = total_pecas

    def _to_utc(dt):
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    for d in spark_dates:
        end_dt = datetime.combine(d, datetime.max.time(), tzinfo=timezone.utc)
        spark_produtos_list.append(sum(1 for c in produtos_created if c is not None and _to_utc(c) <= end_dt))
        spark_insumos_list.append(sum(1 for c in insumos_created if c is not None and _to_utc(c) <= end_dt))
    spark_pecas_list = [pecas_total] * 7

    spark_produtos = ','.join(str(x) for x in spark_produtos_list)
    spark_pecas = ','.join(str(x) for x in spark_pecas_list)
    spark_insumos = ','.join(str(x) for x in spark_insumos_list)

    ve_rounded = round(valor_estoque, 2)
    spark_valor_estoque = ','.join(str(ve_rounded) for _ in spark_dates)
    spark_saude = ','.join(str(ok_count) for _ in spark_dates)

    # Metas do período
    hoje_d = date.today()
    todas_metas = Meta.query.all()
    metas_ativas = sum(1 for m in todas_metas if not m.concluida and m.data_ini <= hoje_d and m.data_fim >= hoje_d)
    metas_concluidas = sum(1 for m in todas_metas if m.concluida)
    metas_total = len(todas_metas)
    metas_progresso = 0
    if metas_total > 0:
        soma_pct = sum(min(m.valor_atual / m.valor_meta, 1) for m in todas_metas if m.valor_meta > 0)
        metas_com_valor = sum(1 for m in todas_metas if m.valor_meta > 0)
        if metas_com_valor > 0:
            metas_progresso = min(round(soma_pct / metas_com_valor * 100, 1), 100)
        else:
            metas_progresso = 100

    return render_template(
        'index.html',
        total_produtos=total_produtos,
        total_pecas=total_pecas,
        spark_pecas=spark_pecas,
        total_insumos=total_insumos,
        total_itens=total_itens,
        total_vendas=total_vendas,
        var_faturamento=var_faturamento,
        var_lucro=var_lucro,
        ticket_medio=ticket_medio,
        valor_periodo=round(valor_periodo, 2),
        lucro_periodo=round(lucro_periodo, 2),
        valor_estoque=ve_rounded,
        produtos_baixo_estoque=produtos_baixo_estoque,
        data_ini=ini,
        data_fim=fim,
        cat_labels=cat_labels,
        cat_data=cat_data,
        vendas_labels=vendas_labels,
        vendas_data=vendas_data,
        media_diaria=round(valor_periodo / max((fim - ini).days + 1, 1), 2),
        produtos_baixo_count=len(produtos_baixo_estoque),
        top_prod_labels=top_prod_labels,
        top_prod_data=top_prod_data,
        top_prod_valores=top_prod_valores,
        ultimas_vendas=ultimas_vendas,
        saude_ok=ok_count,
        saude_baixo=baixo_count,
        saude_zerado=zerado_count,
        spark_produtos=spark_produtos,
        spark_insumos=spark_insumos,
        spark_vendas=spark_vendas,
        spark_faturamento=spark_faturamento,
        spark_valor_estoque=spark_valor_estoque,
        spark_saude=spark_saude,
        metas_ativas=metas_ativas,
        metas_concluidas=metas_concluidas,
        metas_total=metas_total,
        metas_progresso=metas_progresso,
        format_br=format_br,
    )


@bp.route('/backups')
def listar_backups():
    from app.services.backup import listar_backups, BACKUP_DIR
    backups = listar_backups()
    return render_template('backups.html', backups=backups)


@bp.route('/backup/criar', methods=['POST'])
def criar_backup():
    from app.services.backup import criar_backup
    nome = criar_backup()
    if nome:
        flash(f'Backup criado: {nome}', 'success')
    else:
        flash('Nenhum banco para backup.', 'warning')
    return redirect(url_for('dashboard.listar_backups'))


@bp.route('/backup/<nome>/baixar')
def baixar_backup(nome):
    from app.services.backup import BACKUP_DIR
    caminho = os.path.normpath(os.path.join(BACKUP_DIR, nome))
    try:
        if os.path.commonpath([caminho, BACKUP_DIR]) != BACKUP_DIR:
            flash('Acesso negado.', 'danger')
            return redirect(url_for('dashboard.listar_backups'))
    except ValueError:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard.listar_backups'))
    if not os.path.exists(caminho):
        flash('Backup não encontrado.', 'danger')
        return redirect(url_for('dashboard.listar_backups'))
    return send_file(caminho, as_attachment=True)


@bp.route('/exportar/csv')
def exportar_csv():
    hoje = date.today()
    fim = datetime.strptime(request.args.get('data_fim', hoje.isoformat()), '%Y-%m-%d').date()
    ini = datetime.strptime(request.args.get('data_ini', (hoje - timedelta(days=30)).isoformat()), '%Y-%m-%d').date()
    vendas = Venda.query.options(subqueryload(Venda.itens)).filter(
        Venda.data_venda >= ini, Venda.data_venda <= fim
    ).order_by(Venda.data_venda.desc(), Venda.created_at.desc()).all()
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(['Data', 'Produto', 'Qtd', 'Valor Unit.', 'Total', 'Forma Pagto.', 'Taxa %', 'Taxa R$', 'Cliente'])
    for v in vendas:
        for item in v.itens:
            w.writerow([
                v.data_venda.isoformat(),
                item.produto.nome if item.produto else 'Removido',
                item.qtd, item.preco_unitario,
                round(item.qtd * item.preco_unitario, 2),
                v.forma_pagamento or '', v.taxa_percentual or 0,
                v.taxa_valor or 0, v.cliente_nome or '',
            ])
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=vendas.csv'}
    )


@bp.route('/api/ngrok-status')
def ngrok_status():
    from flask import jsonify, request
    host = request.host
    is_ngrok = 'ngrok' in host or 'ngrok-free' in host
    return jsonify({'via_ngrok': is_ngrok})
