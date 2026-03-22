from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User, Client
from app.forms import LoginForm, RegistrationForm, ClientRegistrationForm
from app.utils import send_email

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Неверное имя пользователя или пароль.', 'danger')
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if current_user.role != 'admin':
        flash('Доступ запрещён.', 'danger')
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Пользователь зарегистрирован.', 'success')
        return redirect(url_for('admin.users'))
    return render_template('auth/register.html', form=form)

@bp.route('/client/register', methods=['GET', 'POST'])
def client_register():
    form = ClientRegistrationForm()
    if form.validate_on_submit():
        client = Client(username=form.username.data, email=form.email.data,
                        phone=form.phone.data, address=form.address.data)
        client.set_password(form.password.data)
        db.session.add(client)
        db.session.commit()
        flash('Регистрация успешна. Теперь вы можете войти.', 'success')
        return redirect(url_for('auth.client_login'))
    return render_template('auth/client_register.html', form=form)

@bp.route('/client/login', methods=['GET', 'POST'])
def client_login():
    if 'client_id' in request.cookies:
        # Упрощённая аутентификация клиента через cookie, но лучше использовать отдельную сессию
        pass
    form = LoginForm()
    if form.validate_on_submit():
        client = Client.query.filter_by(username=form.username.data).first()
        if client and client.check_password(form.password.data) and client.is_active:
            # Используем простую cookie для демонстрации, в реальности нужна отдельная сессия
            resp = redirect(url_for('client.dashboard'))
            resp.set_cookie('client_id', str(client.id), httponly=True, secure=True)
            flash('Добро пожаловать в личный кабинет!', 'success')
            return resp
        else:
            flash('Неверные данные.', 'danger')
    return render_template('auth/client_login.html', form=form)

@bp.route('/client/logout')
def client_logout():
    resp = redirect(url_for('main.index'))
    resp.delete_cookie('client_id')
    flash('Вы вышли из кабинета.', 'info')
    return resp