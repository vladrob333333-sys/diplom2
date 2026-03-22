from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Ticket, User, Client, Service
from app.forms import TicketForm, AssignTicketForm
from app.utils import send_email
from datetime import datetime
from sqlalchemy import func

bp = Blueprint('operator', __name__, url_prefix='/operator')

def operator_required(f):
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role not in ['operator', 'admin']:
            abort(403)
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@bp.route('/dashboard')
@operator_required
def dashboard():
    # Статистика для оператора
    tickets_total = Ticket.query.count()
    tickets_new = Ticket.query.filter_by(status='new').count()
    tickets_in_progress = Ticket.query.filter_by(status='in_progress').count()
    tickets_completed = Ticket.query.filter_by(status='completed').count()
    return render_template('operator/dashboard.html',
                           tickets_total=tickets_total,
                           tickets_new=tickets_new,
                           tickets_in_progress=tickets_in_progress,
                           tickets_completed=tickets_completed)

@bp.route('/tickets')
@operator_required
def tickets():
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    return render_template('operator/tickets.html', tickets=tickets)

@bp.route('/create_ticket', methods=['GET', 'POST'])
@operator_required
def create_ticket():
    form = TicketForm()
    form.service_id.choices = [(s.id, s.name) for s in Service.query.filter_by(is_active=True).all()]
    form.client_id.choices = [(c.id, c.username) for c in Client.query.filter_by(is_active=True).all()]
    form.assigned_to_id.choices = [(0, 'Не назначать')] + [(u.id, u.username) for u in User.query.filter_by(role='executor', is_active=True).all()]
    if form.validate_on_submit():
        ticket = Ticket(
            title=form.title.data,
            description=form.description.data,
            priority=form.priority.data,
            service_id=form.service_id.data,
            client_id=form.client_id.data,
            created_by_id=current_user.id
        )
        if form.assigned_to_id.data != 0:
            ticket.assigned_to_id = form.assigned_to_id.data
            ticket.status = 'assigned'
            # Уведомление исполнителю
            executor = User.query.get(form.assigned_to_id.data)
            if executor:
                send_email('Новая заявка', [executor.email],
                           f'Вам назначена заявка "{ticket.title}". Подробнее в системе.')
        db.session.add(ticket)
        db.session.commit()
        flash('Заявка создана.', 'success')
        return redirect(url_for('operator.tickets'))
    return render_template('operator/create_ticket.html', form=form)

@bp.route('/assign_ticket/<int:ticket_id>', methods=['GET', 'POST'])
@operator_required
def assign_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.status != 'new':
        flash('Заявка уже назначена или закрыта.', 'warning')
        return redirect(url_for('operator.tickets'))
    form = AssignTicketForm()
    form.assigned_to_id.choices = [(u.id, u.username) for u in User.query.filter_by(role='executor', is_active=True).all()]
    if form.validate_on_submit():
        ticket.assigned_to_id = form.assigned_to_id.data
        ticket.status = 'assigned'
        db.session.commit()
        executor = User.query.get(form.assigned_to_id.data)
        if executor:
            send_email('Назначена заявка', [executor.email],
                       f'Вам назначена заявка "{ticket.title}". Подробнее в системе.')
        flash('Заявка назначена.', 'success')
        return redirect(url_for('operator.tickets'))
    return render_template('operator/assign_ticket.html', form=form, ticket=ticket)

@bp.route('/charts')
@operator_required
def charts():
    # Получение данных для диаграмм по статусам
    statuses = ['new', 'assigned', 'in_progress', 'completed', 'cancelled', 'rejected']
    data = []
    for status in statuses:
        count = Ticket.query.filter_by(status=status).count()
        data.append(count)
    # Данные по исполнителям
    executors = User.query.filter_by(role='executor').all()
    executor_data = {}
    for exec in executors:
        executor_data[exec.username] = Ticket.query.filter_by(assigned_to_id=exec.id).count()
    return render_template('operator/charts.html', status_data=data, status_labels=statuses, executor_data=executor_data)