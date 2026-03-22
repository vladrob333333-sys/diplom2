from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Ticket, User, Comment
from app.forms import CommentForm
from app.utils import send_email
from datetime import datetime
from sqlalchemy import func

bp = Blueprint('executor', __name__, url_prefix='/executor')

def executor_required(f):
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != 'executor':
            abort(403)
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@bp.route('/dashboard')
@executor_required
def dashboard():
    my_tickets = Ticket.query.filter_by(assigned_to_id=current_user.id).order_by(Ticket.created_at.desc()).all()
    available_tickets = Ticket.query.filter_by(status='new').all()
    return render_template('executor/dashboard.html', my_tickets=my_tickets, available_tickets=available_tickets)

@bp.route('/available_tickets')
@executor_required
def available_tickets():
    tickets = Ticket.query.filter_by(status='new').order_by(Ticket.created_at.asc()).all()
    return render_template('executor/available_tickets.html', tickets=tickets)

@bp.route('/accept_ticket/<int:ticket_id>')
@executor_required
def accept_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.status != 'new':
        flash('Заявка уже назначена или закрыта.', 'warning')
        return redirect(url_for('executor.available_tickets'))
    ticket.assigned_to_id = current_user.id
    ticket.status = 'assigned'
    db.session.commit()
    # Уведомление оператору
    if ticket.creator:
        send_email('Заявка принята', [ticket.creator.email],
                   f'Исполнитель {current_user.username} принял заявку "{ticket.title}".')
    flash('Заявка принята.', 'success')
    return redirect(url_for('executor.my_tickets'))

@bp.route('/my_tickets')
@executor_required
def my_tickets():
    tickets = Ticket.query.filter_by(assigned_to_id=current_user.id).order_by(Ticket.created_at.desc()).all()
    return render_template('executor/my_tickets.html', tickets=tickets)

@bp.route('/reject_ticket/<int:ticket_id>')
@executor_required
def reject_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.assigned_to_id != current_user.id or ticket.status not in ['assigned', 'in_progress']:
        flash('Невозможно отказаться от заявки.', 'warning')
        return redirect(url_for('executor.my_tickets'))
    ticket.status = 'rejected'
    ticket.assigned_to_id = None
    db.session.commit()
    # Уведомление оператору
    if ticket.creator:
        send_email('Отказ от заявки', [ticket.creator.email],
                   f'Исполнитель {current_user.username} отказался от заявки "{ticket.title}".')
    flash('Вы отказались от заявки.', 'info')
    return redirect(url_for('executor.my_tickets'))

@bp.route('/start_ticket/<int:ticket_id>')
@executor_required
def start_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.assigned_to_id != current_user.id or ticket.status != 'assigned':
        flash('Невозможно начать выполнение.', 'warning')
        return redirect(url_for('executor.my_tickets'))
    ticket.status = 'in_progress'
    db.session.commit()
    flash('Заявка взята в работу.', 'success')
    return redirect(url_for('executor.my_tickets'))

@bp.route('/complete_ticket/<int:ticket_id>', methods=['GET', 'POST'])
@executor_required
def complete_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.assigned_to_id != current_user.id or ticket.status != 'in_progress':
        flash('Невозможно завершить заявку.', 'warning')
        return redirect(url_for('executor.my_tickets'))
    if request.method == 'POST':
        ticket.status = 'completed'
        ticket.completed_at = datetime.utcnow()
        db.session.commit()
        flash('Заявка завершена.', 'success')
        return redirect(url_for('executor.my_tickets'))
    return render_template('executor/complete_ticket.html', ticket=ticket)

@bp.route('/charts')
@executor_required
def charts():
    # Диаграммы только для своих заявок
    statuses = ['new', 'assigned', 'in_progress', 'completed', 'cancelled', 'rejected']
    data = []
    for status in statuses:
        count = Ticket.query.filter_by(assigned_to_id=current_user.id, status=status).count()
        data.append(count)
    # Данные по месяцам
    monthly = db.session.query(func.strftime('%Y-%m', Ticket.created_at), func.count()).filter_by(assigned_to_id=current_user.id).group_by(func.strftime('%Y-%m', Ticket.created_at)).all()
    return render_template('executor/charts.html', status_data=data, status_labels=statuses, monthly=monthly)