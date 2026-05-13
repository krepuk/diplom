from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# ЗАГРУЗЧИК ПОЛЬЗОВАТЕЛЯ ДЛЯ FLASK-LOGIN
@login_manager.user_loader
def load_user(id):
    """Flask-Login использует эту функцию для получения пользователя по ID из сессии"""
    return User.query.get(int(id))


# МОДЕЛЬ ПОЛЬЗОВАТЕЛЯ
class User(UserMixin, db.Model):
    """Сотрудник или пользователь системы с разными ролями"""
    
    # Базовые поля
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)  
    phone = db.Column(db.String(20), nullable=False)               
    password_hash = db.Column(db.String(128))
    
    # Ролевая система: employee (обычный), support, superadmin
    role = db.Column(db.String(20), default='employee') 
    
    department = db.Column(db.String(50)) 

    # Связи с тикетами
    tickets_created = db.relationship(
        'Ticket', 
        foreign_keys='Ticket.creator_id',  # Тикеты, где пользователь - автор
        backref='creator', 
        lazy='dynamic'
    )
    tickets_assigned = db.relationship(
        'Ticket', 
        foreign_keys='Ticket.assignee_id',  # Тикеты, где пользователь - исполнитель
        backref='assignee', 
        lazy='dynamic'
    )

    # Хеширование пароля
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# МОДЕЛЬ ТИКЕТА (ЗАЯВКИ)
class Ticket(db.Model):
    """Заявка в техподдержку с жизненным циклом: Новая → В работе → Решена → Закрыта"""
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # Участок
    priority = db.Column(db.String(20), default='Средний')  # Низкий/Средний/Высокий/Критический
    status = db.Column(db.String(20), default='Новая')  # Новая/В работе/Решена/Закрыта
    reopen_count = db.Column(db.Integer, default=0)  # Счетчик переоткрытий (для эскалации)
    
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime, nullable=True)  # Время окончательного закрытия
    
    # Внешние ключи
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Кто создал
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Кто исполняет
    
    # Связи
    comments = db.relationship('Comment', backref='ticket', lazy='dynamic', cascade='all, delete')
    
    # ===== ВЫЧИСЛЯЕМЫЕ СВОЙСТВА =====
    @property
    def comment_count(self):
        """Общее количество комментариев в заявке"""
        return self.comments.count()

    def has_new_reply(self, current_user_id):
        """
        Проверяет, есть ли новый ответ (последний комментарий написан не текущим пользователем)
        Используется для подсветки диалога, где нужно ответить
        """
        last_comment = self.comments.order_by(Comment.created_at.desc()).first()
        if last_comment and last_comment.author_id != current_user_id:
            return True
        return False


# МОДЕЛЬ КОММЕНТАРИЯ
class Comment(db.Model):
    """Комментарии к тикету (обсуждение)"""
    
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Внешние ключи
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    
    # Связи
    author = db.relationship('User', backref='comments')


# МОДЕЛЬ СТАТЬИ БАЗЫ ЗНАНИЙ
class Article(db.Model):
    """Статья в базе знаний (FAQ/инструкция)"""
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)   # Вопрос/заголовок
    content = db.Column(db.Text, nullable=False)        # Развернутый ответ
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Внешний ключ
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Связи
    author = db.relationship('User', backref='articles_created')