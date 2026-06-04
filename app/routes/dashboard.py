from datetime import date, timedelta, datetime, timezone
from sqlalchemy import func
from flask import Blueprint, render_template, request
from app.extensions import db
from app.models.produto import Produto
from app.models.insumo import Insumo
from app.models.categoria import Categoria
from app.models.venda import Venda
from app.models.venda_item import VendaItem

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
        'data_ini', (hoje - timedelta(days=30)).isoformat()), '%Y-%m-%d').date()

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

    # Valor total em estoque (custo_producao * qtd_estoque)
    valor_estoque = db.session.query(
        func.sum(Produto.preco_venda * Produto.qtd_estoque)
    ).filter(Produto.ativo == True).scalar() or 0

    # Saúde do estoque
    ok_count = Produto.query.filter(Produto.ativo == True, Produto.qtd_estoque > 10).count()
    baixo_count = Produto.query.filter(Produto.ativo == True, Produto.qtd_estoque >= 1, Produto.qtd_estoque <= 10).count()
    zerado_count = Produto.query.filter(Produto.ativo == True, Produto.qtd_estoque == 0).count()

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
    ultimas_vendas = Venda.query.order_by(Venda.created_at.desc()).limit(5).all()

    produtos_baixo_estoque = Produto.query.filter(
        Produto.ativo == True, Produto.qtd_estoque <= 5
    ).order_by(Produto.qtd_estoque.asc()).all()

    categorias = Categoria.query.all()
    cat_labels = []
    cat_data = []
    for cat in categorias:
        count = Produto.query.filter_by(categoria_id=cat.id, ativo=True).count()
        if count > 0:
            cat_labels.append(cat.nome)
            cat_data.append(count)

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
    for d in spark_dates:
        day_vendas = Venda.query.filter(Venda.data_venda == d).all()
        spark_vendas_list.append(len(day_vendas))
        spark_faturamento_list.append(round(sum(v.valor_total for v in day_vendas), 2))

    spark_vendas = ','.join(str(x) for x in spark_vendas_list)
    spark_faturamento = ','.join(str(x) for x in spark_faturamento_list)

    spark_produtos_list = []
    spark_pecas_list = []
    spark_insumos_list = []
    for d in spark_dates:
        end_dt = datetime.combine(d, datetime.max.time()).replace(tzinfo=timezone.utc)
        spark_produtos_list.append(Produto.query.filter(
            Produto.ativo == True, Produto.created_at <= end_dt).count())
        pecas_qtd = db.session.query(func.sum(Produto.qtd_estoque)).filter(
            Produto.ativo == True, Produto.created_at <= end_dt).scalar() or 0
        spark_pecas_list.append(pecas_qtd)
        spark_insumos_list.append(Insumo.query.filter(
            Insumo.created_at <= end_dt).count())

    spark_produtos = ','.join(str(x) for x in spark_produtos_list)
    spark_pecas = ','.join(str(x) for x in spark_pecas_list)
    spark_insumos = ','.join(str(x) for x in spark_insumos_list)

    ve_rounded = round(valor_estoque, 2)
    spark_valor_estoque = ','.join(str(ve_rounded) for _ in spark_dates)
    spark_saude = ','.join(str(ok_count) for _ in spark_dates)

    return render_template(
        'index.html',
        total_produtos=total_produtos,
        total_pecas=total_pecas,
        spark_pecas=spark_pecas,
        total_insumos=total_insumos,
        total_vendas=total_vendas,
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
        format_br=format_br,
    )
