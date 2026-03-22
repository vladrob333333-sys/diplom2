from app import create_app, db
from app.models import User, Client, Service, Ticket, Comment
import sqlalchemy as sa

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Client': Client, 'Service': Service, 'Ticket': Ticket, 'Comment': Comment}

# Создание таблиц и расширение столбцов password_hash
with app.app_context():
    db.create_all()
    
    if db.engine.dialect.name == 'postgresql':
        # Расширение для users
        try:
            result = db.session.execute(
                sa.text("""
                    SELECT data_type, character_maximum_length 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='password_hash'
                """)
            )
            row = result.fetchone()
            if row and row[1] == 128:
                db.session.execute(sa.text("ALTER TABLE users ALTER COLUMN password_hash TYPE VARCHAR(256);"))
                db.session.commit()
                print("Столбец password_hash в users расширен до VARCHAR(256)")
        except Exception as e:
            print(f"Ошибка при изменении столбца users.password_hash: {e}")
        
        # Расширение для clients
        try:
            result = db.session.execute(
                sa.text("""
                    SELECT data_type, character_maximum_length 
                    FROM information_schema.columns 
                    WHERE table_name='clients' AND column_name='password_hash'
                """)
            )
            row = result.fetchone()
            if row and row[1] == 128:
                db.session.execute(sa.text("ALTER TABLE clients ALTER COLUMN password_hash TYPE VARCHAR(256);"))
                db.session.commit()
                print("Столбец password_hash в clients расширен до VARCHAR(256)")
        except Exception as e:
            print(f"Ошибка при изменении столбца clients.password_hash: {e}")
    
    # Создание администратора
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
