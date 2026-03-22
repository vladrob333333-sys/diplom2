from app import create_app, db
from app.models import User, Client, Service, Ticket, Comment

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Client': Client, 'Service': Service, 'Ticket': Ticket, 'Comment': Comment}

# Создание администратора при первом запуске
with app.app_context():
    db.create_all()
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Администратор создан: admin / admin123")
    else:
        print("Администратор уже существует.")

if __name__ == '__main__':
    app.run(debug=True)
