from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, IntegerField, FloatField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange
from app.models import User, Client, Service

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Роль', choices=[('operator', 'Оператор'), ('executor', 'Исполнитель'), ('admin', 'Администратор')])
    submit = SubmitField('Зарегистрировать')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Имя пользователя уже занято.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email уже зарегистрирован.')

class ClientRegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    phone = StringField('Телефон')
    address = StringField('Адрес')
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        client = Client.query.filter_by(username=username.data).first()
        if client:
            raise ValidationError('Имя пользователя уже занято.')

    def validate_email(self, email):
        client = Client.query.filter_by(email=email.data).first()
        if client:
            raise ValidationError('Email уже зарегистрирован.')

class TicketForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    description = TextAreaField('Описание')
    priority = SelectField('Приоритет', choices=[('low', 'Низкий'), ('medium', 'Средний'), ('high', 'Высокий')], default='medium')
    service_id = SelectField('Услуга', coerce=int, validators=[DataRequired()])
    client_id = SelectField('Клиент', coerce=int, validators=[DataRequired()])
    assigned_to_id = SelectField('Назначить исполнителю', coerce=int, default=0)
    submit = SubmitField('Создать заявку')

class AssignTicketForm(FlaskForm):
    assigned_to_id = SelectField('Назначить исполнителю', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Назначить')

class CommentForm(FlaskForm):
    content = TextAreaField('Отзыв', validators=[DataRequired()])
    rating = IntegerField('Оценка (1-5)', validators=[DataRequired(), NumberRange(min=1, max=5)])
    submit = SubmitField('Отправить')

class ServiceForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание')
    price = FloatField('Цена')
    is_active = BooleanField('Активна')
    submit = SubmitField('Сохранить')

class BackupForm(FlaskForm):
    submit = SubmitField('Создать бэкап')