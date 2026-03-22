import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import login_required, current_user
from app import db
from app.models import User, Client, Service, Ticket, Comment
from app.forms import ServiceForm, BackupForm
from app.utils import create_backup
from werkzeug.utils import secure_filename
import json

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Доступ запрещён.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@bp.route('/dashboard')
@admin_required
def dashboard():
    # Статистика
    users_count = User.query.count()
    clients_count = Client.query.count()
    services_count = Service.query.count()
    tickets_count = Ticket.query.count()
    return render_template('admin/dashboard.html',
                           users_count=users_count,
                           clients_count=clients_count,
                           services_count=services_count,
                           tickets_count=tickets_count)

@bp.route('/users')
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@bp.route('/user/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    # Используем ту же форму, что и при регистрации, но можно сделать отдельную
    form = RegistrationForm(obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('Пользователь обновлён.', 'success')
        return redirect(url_for('admin.users'))
    # Заполняем форму текущими данными
    form.username.data = user.username
    form.email.data = user.email
    form.role.data = user.role
    return render_template('admin/edit_user.html', form=form, user=user)

@bp.route('/user/delete/<int:user_id>')
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Нельзя удалить самого себя.', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('Пользователь удалён.', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/clients')
@admin_required
def clients():
    clients = Client.query.all()
    return render_template('admin/clients.html', clients=clients)

@bp.route('/client/edit/<int:client_id>', methods=['GET', 'POST'])
@admin_required
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    form = ClientRegistrationForm(obj=client)
    if form.validate_on_submit():
        client.username = form.username.data
        client.email = form.email.data
        client.phone = form.phone.data
        client.address = form.address.data
        if form.password.data:
            client.set_password(form.password.data)
        db.session.commit()
        flash('Клиент обновлён.', 'success')
        return redirect(url_for('admin.clients'))
    form.username.data = client.username
    form.email.data = client.email
    form.phone.data = client.phone
    form.address.data = client.address
    return render_template('admin/edit_client.html', form=form, client=client)

@bp.route('/services')
@admin_required
def services():
    services = Service.query.all()
    return render_template('admin/services.html', services=services)

@bp.route('/service/add', methods=['GET', 'POST'])
@admin_required
def add_service():
    form = ServiceForm()
    if form.validate_on_submit():
        service = Service(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            is_active=form.is_active.data
        )
        db.session.add(service)
        db.session.commit()
        flash('Услуга добавлена.', 'success')
        return redirect(url_for('admin.services'))
    return render_template('admin/service_form.html', form=form, title='Добавить услугу')

@bp.route('/service/edit/<int:service_id>', methods=['GET', 'POST'])
@admin_required
def edit_service(service_id):
    service = Service.query.get_or_404(service_id)
    form = ServiceForm(obj=service)
    if form.validate_on_submit():
        service.name = form.name.data
        service.description = form.description.data
        service.price = form.price.data
        service.is_active = form.is_active.data
        db.session.commit()
        flash('Услуга обновлена.', 'success')
        return redirect(url_for('admin.services'))
    return render_template('admin/service_form.html', form=form, title='Редактировать услугу')

@bp.route('/tickets')
@admin_required
def tickets():
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    return render_template('admin/tickets.html', tickets=tickets)

@bp.route('/backup', methods=['GET', 'POST'])
@admin_required
def backup():
    form = BackupForm()
    if form.validate_on_submit():
        json_path, csv_paths = create_backup()
        flash(f'Бэкап создан: {json_path}', 'success')
        # Здесь можно отправить файл пользователю, но для простоты оставим на сервере
    return render_template('admin/backup.html', form=form)