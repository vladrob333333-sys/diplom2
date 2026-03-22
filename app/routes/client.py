from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, make_response
from app import db
from app.models import Client, Ticket, Service, Comment, User
from app.forms import TicketForm, CommentForm
from datetime import datetime
from sqlalchemy import func
import uuid

bp = Blueprint('client', __name__, url_prefix='/client')

def get_current_client():
    # Простая реализация через cookie (в реальности используйте отдельную сессию)
    client_id = request.cookies.get('client_id')
    if client_id:
        return Client.query.get(int(client_id))
    return None

def client_required(f):
    def decorated(*args, **kwargs):
        client = get_current_client()
        if not client:
            abort(401)
        return f(client, *args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@bp.route('/dashboard')
def dashboard():
    client = get_current_client()
    if not client:
        return redirect(url_for('auth.client_login'))
    # Получаем услуги клиента
    services = client.services
    # Последние заявки
    recent_tickets = Ticket.query.filter_by(client_id=client.id).order_by(Ticket.created_at.desc()).limit(5).all()
    return render_template('client/dashboard.html', client=client, services=services, recent_tickets=recent_tickets)

@bp.route('/services')
@client_required
def services(client):
    services = client.services
    return render_template('client/services.html', services=services)

@bp.route('/create_ticket', methods=['GET', 'POST'])
@client_required
def create_ticket(client):
    form = TicketForm()
    form.service_id.choices = [(s.id, s.name) for s in client.services if s.is_active]
    form.client_id.choices = [(client.id, client.username)]
    form.assigned_to_id.choices = [(0, '')]
    del form.assigned_to_id  # Клиент не назначает
    if form.validate_on_submit():
        ticket = Ticket(
            title=form.title.data,
            description=form.description.data,
            priority=form.priority.data,
            service_id=form.service_id.data,
            client_id=client.id,
            created_by_id=1,  # системный пользователь или None
            status='new'
        )
        db.session.add(ticket)
        db.session.commit()
        flash('Заявка создана. Ожидайте назначения.', 'success')
        return redirect(url_for('client.my_tickets'))
    return render_template('client/create_ticket.html', form=form)

@bp.route('/my_tickets')
@client_required
def my_tickets(client):
    tickets = Ticket.query.filter_by(client_id=client.id).order_by(Ticket.created_at.desc()).all()
    return render_template('client/my_tickets.html', tickets=tickets)

@bp.route('/ticket/<int:ticket_id>')
@client_required
def ticket_detail(client, ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.client_id != client.id:
        abort(403)
    # Комментарии к заявке
    comments = Comment.query.filter_by(ticket_id=ticket.id).all()
    form = CommentForm()
    return render_template('client/ticket_detail.html', ticket=ticket, comments=comments, form=form)

@bp.route('/add_comment/<int:ticket_id>', methods=['POST'])
@client_required
def add_comment(client, ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.client_id != client.id or ticket.status != 'completed':
        flash('Отзыв можно оставить только к завершённой заявке.', 'warning')
        return redirect(url_for('client.ticket_detail', ticket_id=ticket.id))
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            rating=form.rating.data,
            ticket_id=ticket.id,
            client_id=client.id,
            user_id=ticket.assigned_to_id
        )
        db.session.add(comment)
        db.session.commit()
        flash('Отзыв добавлен.', 'success')
    else:
        flash('Ошибка валидации.', 'danger')
    return redirect(url_for('client.ticket_detail', ticket_id=ticket.id))