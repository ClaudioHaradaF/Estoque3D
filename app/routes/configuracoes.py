from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db
from app.models.taxa_configuracao import TaxaConfiguracao

bp = Blueprint('configuracoes', __name__, url_prefix='/configuracoes')


@bp.route('/taxas', methods=['GET', 'POST'])
def taxas():
    if request.method == 'POST':
        metodos = ['dinheiro', 'credito', 'debito', 'pix']
        for metodo in metodos:
            valor = request.form.get(f'taxa_{metodo}', '').strip()
            if valor == '':
                continue
            try:
                taxa = float(valor.replace(',', '.'))
            except ValueError:
                continue
            config = TaxaConfiguracao.query.filter_by(forma_pagamento=metodo).first()
            if config:
                config.taxa_percentual = taxa
            else:
                config = TaxaConfiguracao(forma_pagamento=metodo, taxa_percentual=taxa)
                db.session.add(config)
        db.session.commit()
        flash('Taxas salvas com sucesso!', 'success')
        return redirect(url_for('configuracoes.taxas'))

    taxas = {t.forma_pagamento: t.taxa_percentual for t in TaxaConfiguracao.query.all()}
    metodos_padrao = {'dinheiro': 0, 'credito': 2.5, 'debito': 1.2, 'pix': 0}
    for k, v in metodos_padrao.items():
        taxas.setdefault(k, v)
    return render_template('configuracoes/taxas.html', taxas=taxas)
