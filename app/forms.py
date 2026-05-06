from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class CreateUserForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email(message='Неверный формат почты')])
    phone = StringField('Телефон', validators=[DataRequired()])
    
    # Выбор роли (варианты будем подставлять динамически в зависимости от того, кто создает)
    role = SelectField('Должность', choices=[], validators=[DataRequired()])
    
    # Отдел (нужен только если создаем админа)
    department = SelectField('Выбор участка', choices=[('', 'Не требуется'), ('Участок №2', 'Участок №2'), ('Участок №3', 'Участок №3'), ('Участок №5', 'Участок №5'), ('Участок №8', 'Участок №8'), ('Участок №10', 'Участок №10'), ('Участок №11', 'Участок №11'), ('Участок №13', 'Участок №13'), ('Участок №18', 'Участок №18')])
    
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Создать пользователя')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Этот логин уже занят.')
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Эта почта уже используется.')

class TicketForm(FlaskForm):
    title = StringField('Тема проблемы', validators=[DataRequired()])
    category = SelectField('Участок', choices=[('Участок №2', 'Участок №2'), ('Участок №3', 'Участок №3'), ('Участок №5', 'Участок №5'), ('Участок №8', 'Участок №8'), ('Участок №10', 'Участок №10'), ('Участок №11', 'Участок №11'), ('Участок №13', 'Участок №13'), ('Участок №18', 'Участок №18')], 
                            validators=[DataRequired()])
    
    # НОВОЕ ПОЛЕ В ФОРМЕ
    priority = SelectField('Приоритет проблемы', choices=[
        ('Низкий', 'Низкий'), 
        ('Средний', 'Средний'), 
        ('Высокий', 'Высокий'), 
        ('Критический', 'Критический')
    ], validators=[DataRequired()])
    
    description = TextAreaField('Описание проблемы', validators=[DataRequired()])
    submit = SubmitField('Создать заявку')

class ArticleForm(FlaskForm):
    title = StringField('Вопрос (или заголовок проблемы)', validators=[DataRequired()])
    content = TextAreaField('Решение (подробное описание)', validators=[DataRequired()])
    submit = SubmitField('Добавить в базу знаний')

class CommentForm(FlaskForm):
    text = TextAreaField('Написать комментарий...', validators=[DataRequired()])
    submit = SubmitField('Отправить')