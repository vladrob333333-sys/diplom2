import json
import csv
import os
from datetime import datetime
from flask import current_app
from flask_mail import Message
from app import mail

def send_email(subject, recipients, body):
    """Отправка email-уведомления"""
    try:
        msg = Message(subject, recipients=recipients)
        msg.body = body
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Ошибка отправки email: {e}")
        return False

def create_backup():
    """Создание бэкапа в формате JSON и CSV"""
    from app.models import db, User, Client, Service, Ticket, Comment
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(current_app.root_path, 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    # Сбор данных
    tables = {
        'users': User.query.all(),
        'clients': Client.query.all(),
        'services': Service.query.all(),
        'tickets': Ticket.query.all(),
        'comments': Comment.query.all()
    }

    # JSON бэкап
    json_path = os.path.join(backup_dir, f'backup_{timestamp}.json')
    data = {}
    for name, rows in tables.items():
        data[name] = [row.__dict__ for row in rows]
        for row in data[name]:
            row.pop('_sa_instance_state', None)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    # CSV бэкапы
    for name, rows in tables.items():
        if not rows:
            continue
        csv_path = os.path.join(backup_dir, f'{name}_{timestamp}.csv')
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            # Получаем колонки из первого объекта
            attrs = [k for k in rows[0].__dict__.keys() if not k.startswith('_')]
            writer.writerow(attrs)
            for row in rows:
                writer.writerow([getattr(row, attr) for attr in attrs])

    return json_path, csv_path

def get_chart_data(model, filters=None, date_from=None, date_to=None, group_by='status'):
    """Получение данных для диаграммы (упрощённо)"""
    # Реализуйте в зависимости от модели
    pass