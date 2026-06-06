from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db, admin_required
from app.models.usuario import Usuario

bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')


@bp.route('/')
@admin_required
def listar():
    usuarios = Usuario.query.order_by(Usuario.email).all()
    return render_template('usuarios/listar.html', usuarios=usuarios)


@bp.route('/novo', methods=['GET', 'POST'])
@admin_required
def novo():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('password', '')

        if not email or not senha:
            flash('E-mail e senha são obrigatórios.', 'danger')
            return render_template('usuarios/form.html', usuario=None)

        if Usuario.query.filter_by(email=email).first():
            flash('Já existe um usuário com este e-mail.', 'danger')
            return render_template('usuarios/form.html', usuario=None)

        usuario = Usuario(email=email)
        usuario.set_password(senha)
        db.session.add(usuario)
        db.session.commit()
        flash(f'Usuário {email} cadastrado com sucesso!', 'success')
        return redirect(url_for('usuarios.listar'))

    return render_template('usuarios/form.html', usuario=None)


@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@admin_required
def editar(id):
    usuario = Usuario.query.get_or_404(id)
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('password', '')

        if not email:
            flash('E-mail é obrigatório.', 'danger')
            return render_template('usuarios/form.html', usuario=usuario)

        existente = Usuario.query.filter_by(email=email).first()
        if existente and existente.id != id:
            flash('Já existe um usuário com este e-mail.', 'danger')
            return render_template('usuarios/form.html', usuario=usuario)

        usuario.email = email
        if senha:
            usuario.set_password(senha)
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('usuarios.listar'))

    return render_template('usuarios/form.html', usuario=usuario)


@bp.route('/<int:id>/excluir', methods=['POST'])
@admin_required
def excluir(id):
    usuario = Usuario.query.get_or_404(id)
    if usuario.email == 'harborio3d@gmail.com':
        flash('Não é possível excluir o administrador principal.', 'danger')
        return redirect(url_for('usuarios.listar'))
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('usuarios.listar'))
