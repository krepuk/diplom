from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, ValidationError
from app.models import User

# ФОРМА АВТОРИЗАЦИИ
class LoginForm(FlaskForm):
    """Простая форма входа в систему"""
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


# ФОРМА СОЗДАНИЯ ПОЛЬЗОВАТЕЛЯ (только для суперадмина)
class CreateUserForm(FlaskForm):
    """Форма регистрации новых сотрудников. Доступна только суперадмину."""
    
    username = StringField('Логин', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email(message='Неверный формат почты')])
    phone = StringField('Телефон', validators=[DataRequired()])
    
    # Выбор роли (варианты подставляются динамически в route)
    # choices=[] будет заполнено в зависимости от прав создающего
    role = SelectField('Должность', choices=[], validators=[DataRequired()])
    
    # Отдел (нужен только для роли 'support')
    # Список участков 
    department = SelectField(
        'Выбор участка', 
        choices=[
            ('', 'Не требуется'), 
            ('Участок №2', 'Участок №2'), 
            ('Участок №3', 'Участок №3'), 
            ('Участок №5', 'Участок №5'), 
            ('Участок №8', 'Участок №8'), 
            ('Участок №10', 'Участок №10'), 
            ('Участок №11', 'Участок №11'), 
            ('Участок №13', 'Участок №13'), 
            ('Участок №18', 'Участок №18')
        ]
    )
    
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Создать пользователя')

    # Валидация: проверка уникальности логина
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Этот логин уже занят.')
    
    # Валидация: проверка уникальности email        
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Эта почта уже используется.')


# ФОРМА СОЗДАНИЯ ТИКЕТА
class TicketForm(FlaskForm):
    """Форма для создания новой заявки в техподдержку"""
    
    title = StringField('Тема проблемы', validators=[DataRequired()])
    
    # Категория = участок (список фиксированный)
    category = SelectField(
        'Участок', 
        choices=[
            ('Участок №2', 'Участок №2'), 
            ('Участок №3', 'Участок №3'), 
            ('Участок №5', 'Участок №5'), 
            ('Участок №8', 'Участок №8'), 
            ('Участок №10', 'Участок №10'), 
            ('Участок №11', 'Участок №11'), 
            ('Участок №13', 'Участок №13'), 
            ('Участок №18', 'Участок №18')
        ], 
        validators=[DataRequired()]
    )
    
    # 4 уровня приоритета для SLA и эскалации
    priority = SelectField(
        'Приоритет проблемы', 
        choices=[
            ('Низкий', 'Низкий'),      # Не срочно, можно отложить
            ('Средний', 'Средний'),     # Стандартный приоритет
            ('Высокий', 'Высокий'),     # Срочно, требует внимания
            ('Критический', 'Критический')  # Авария, эскалация на суперадмина
        ], 
        validators=[DataRequired()]
    )
    
    description = TextAreaField('Описание проблемы', validators=[DataRequired()])
    submit = SubmitField('Создать заявку')


# ФОРМА ДЛЯ БАЗЫ ЗНАНИЙ
class ArticleForm(FlaskForm):
    """Форма создания/редактирования статьи в базе знаний"""
    title = StringField('Вопрос (или заголовок проблемы)', validators=[DataRequired()])
    content = TextAreaField('Решение (подробное описание)', validators=[DataRequired()])
    submit = SubmitField('Добавить в базу знаний')


# ФОРМА КОММЕНТАРИЯ
class CommentForm(FlaskForm):
    """Форма добавления комментария к тикету"""
    text = TextAreaField('Написать комментарий...', validators=[DataRequired()])
    submit = SubmitField('Отправить')